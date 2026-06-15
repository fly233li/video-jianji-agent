import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './styles/global.css'

const app = createApp(App)

// Global error handler — catch Vue rendering errors
app.config.errorHandler = (err, _instance, info) => {
  console.error('[Vue Error]', err, info)
}

app.use(createPinia())
app.use(ElementPlus)
app.use(router)
app.mount('#app')
