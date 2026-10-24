import './style.css'
import 'highlight.js/styles/atom-one-dark.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

createApp(App).use(router).mount('#app')
