# backend/analysis/tasks.py
from celery import shared_task
from players.models import Player
from games.models import Game
from players.services import ChessComAPI
from datetime import datetime
import time

@shared_task
def test_analysis_task(player_username):
    """مهمة اختبار بسيطة للتأكد من عمل Celery"""
    time.sleep(2)  # محاكاة معالجة
    return f"تم اختبار تحليل بيانات اللاعب {player_username} بنجاح"

@shared_task
def fetch_player_games(username: str):
    """مهمة مؤقتة مبسطة - سنطورها لاحقاً"""
    try:
        # للآن، سنقوم بإنشاء لاعب فقط
        player, created = Player.objects.get_or_create(
            username=username,
            defaults={
                'full_name': f'اللاعب {username}',
                'country': 'DZ'
            }
        )
        
        return {
            'success': True,
            'message': f'تم إنشاء اللاعب {username}',
            'games_count': 0  # سنضيف جلب المباريات لاحقاً
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
