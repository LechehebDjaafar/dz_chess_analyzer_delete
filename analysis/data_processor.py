from typing import Dict, List
from players.models import Player, PlayerStats, OpeningStat
from games.models import Game
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class GameDataProcessor:
    """معالج بيانات المباريات وتحديث الإحصاءات"""
    
    def __init__(self):
        self.opening_stats = defaultdict(lambda: {'games': 0, 'wins': 0, 'losses': 0, 'draws': 0})
    
    def process_games_batch(self, player: Player, games_data: List[Dict]) -> Dict:
        """معالجة مجموعة من المباريات وتحديث الإحصاءات"""
        processed_count = 0
        skipped_count = 0
        new_openings = 0
        
        for game_data in games_data:
            try:
                success = self._process_single_game(player, game_data)
                if success:
                    processed_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                logger.error(f"خطأ في معالجة مباراة للاعب {player.username}: {e}")
                skipped_count += 1
        
        # تحديث إحصاءات الافتتاحات
        new_openings = self._update_opening_stats(player)
        
        # تحديث الإحصاءات العامة
        self._update_player_stats(player)
        
        return {
            'processed': processed_count,
            'skipped': skipped_count,
            'new_openings': new_openings,
            'success': processed_count > 0
        }
    
    def _process_single_game(self, player: Player, game_data: Dict) -> bool:
        """معالجة مباراة واحدة"""
        try:
            # التحقق من البيانات الأساسية
            if not game_data or 'pgn' not in game_data:
                return False
            
            pgn_content = game_data['pgn']
            if not pgn_content:
                return False
            
            # استخراج معلومات المباراة
            game_info = self._extract_game_info(pgn_content, player.username)
            if not game_info:
                return False
            
            # التحقق من عدم تكرار المباراة
            exists = Game.objects.filter(
                player=player,
                opponent_name=game_info['opponent'],
                date_played=game_info['date'],
                time_control=game_info['time_control']
            ).exists()
            
            if exists:
                return False
            
            # إنشاء سجل المباراة
            Game.objects.create(
                player=player,
                opponent_name=game_info['opponent'],
                opponent_rating=game_data.get('opponent_rating'),
                pgn_content=pgn_content,
                result=game_info['result'],
                date_played=game_info['date'],
                time_control=game_info['time_control'],
                player_color=game_info['player_color'],
                opening_name=game_info.get('opening_name', ''),
                opening_eco=game_info.get('opening_eco', ''),
                moves_count=game_info.get('moves_count', 0),
                game_url=game_data.get('url', '')
            )
            
            return True
            
        except Exception as e:
            logger.error(f"خطأ في معالجة مباراة واحدة: {e}")
            return False
    
    def _extract_game_info(self, pgn_content: str, username: str) :
        """استخراج معلومات المباراة من PGN"""
        from players.chess_api import ChessComAPI
        
        api = ChessComAPI()
        game_info = api.parse_pgn_info(pgn_content, username)
        
        if game_info:
            # إضافة معلومات الافتتاح
            opening_name, eco_code = api.extract_opening_name(pgn_content)
            game_info['opening_name'] = opening_name
            game_info['opening_eco'] = eco_code
        
        return game_info
    
    def _update_opening_stats(self, player: Player) -> int:
        """تحديث إحصاءات الافتتاحات"""
        games = Game.objects.filter(player=player)
        opening_stats = defaultdict(lambda: {
            'games': 0, 'wins': 0, 'losses': 0, 'draws': 0, 
            'as_white': 0, 'as_black': 0
        })
        
        # حساب الإحصاءات من المباريات
        for game in games:
            if not game.opening_name or game.opening_name == 'غير معروف':
                continue
            
            key = (game.opening_name, game.opening_eco)
            stats = opening_stats[key]
            
            stats['games'] += 1
            
            # تحديد اللون
            if game.player_color == 'white':
                stats['as_white'] += 1
            else:
                stats['as_black'] += 1
            
            # تحديد النتيجة
            if game.player_won:
                stats['wins'] += 1
            elif game.is_draw:
                stats['draws'] += 1
            else:
                stats['losses'] += 1
        
        # تحديث قاعدة البيانات
        new_openings_count = 0
        for (opening_name, eco_code), stats in opening_stats.items():
            # تحديد اللون الغالب
            if stats['as_white'] > stats['as_black']:
                color_played = 'white'
            elif stats['as_black'] > stats['as_white']:
                color_played = 'black'
            else:
                color_played = 'both'
            
            opening_stat, created = OpeningStat.objects.get_or_create(
                player=player,
                opening_name=opening_name,
                eco_code=eco_code,
                defaults={
                    'games_played': stats['games'],
                    'wins': stats['wins'],
                    'losses': stats['losses'],
                    'draws': stats['draws'],
                    'color_played': color_played
                }
            )
            
            if not created:
                # تحديث الإحصاءات الموجودة
                opening_stat.games_played = stats['games']
                opening_stat.wins = stats['wins']
                opening_stat.losses = stats['losses']
                opening_stat.draws = stats['draws']
                opening_stat.color_played = color_played
                opening_stat.save()
            else:
                new_openings_count += 1
        
        return new_openings_count
    
    def _update_player_stats(self, player: Player):
        """تحديث إحصاءات اللاعب العامة"""
        games = Game.objects.filter(player=player)
        total_games = games.count()
        
        if total_games == 0:
            return
        
        wins = sum(1 for game in games if game.player_won)
        draws = sum(1 for game in games if game.is_draw)
        losses = total_games - wins - draws
        
        # البحث عن الافتتاح المفضل
        favorite_opening = OpeningStat.objects.filter(
            player=player
        ).order_by('-games_played').first()
        
        # البحث عن أضعف دفاع
        weakest_defense = OpeningStat.objects.filter(
            player=player,
            games_played__gte=3
        ).order_by('win_rate').first()
        
        # متوسط طول المباراة
        total_moves = sum(game.moves_count for game in games if game.moves_count > 0)
        games_with_moves = games.filter(moves_count__gt=0).count()
        avg_length = total_moves // games_with_moves if games_with_moves > 0 else 0
        
        # تحديث الإحصاءات
        stats, created = PlayerStats.objects.get_or_create(
            player=player,
            defaults={
                'total_games': total_games,
                'wins': wins,
                'losses': losses,
                'draws': draws,
                'favorite_opening': favorite_opening.opening_name if favorite_opening else '',
                'weakest_defense': weakest_defense.opening_name if weakest_defense else '',
                'average_game_length': avg_length,
                'last_analysis': datetime.now()
            }
        )
        
        if not created:
            stats.total_games = total_games
            stats.wins = wins
            stats.losses = losses
            stats.draws = draws
            stats.favorite_opening = favorite_opening.opening_name if favorite_opening else ''
            stats.weakest_defense = weakest_defense.opening_name if weakest_defense else ''
            stats.average_game_length = avg_length
            stats.last_analysis = datetime.now()
            stats.save()
