import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// استيراد Tailwind CSS
import './style.css'

// استيراد خطوط عربية من Google Fonts
import '@fontsource/cairo/400.css'
import '@fontsource/cairo/600.css' 
import '@fontsource/cairo/700.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
