import Vue from 'vue'
import App from './App.vue'
import {BootstrapVue, IconsPlugin} from 'bootstrap-vue';

import VueNativeWebsocket from 'vue-native-websocket'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'


Vue.config.productionTip = false
Vue.use(BootstrapVue);
Vue.use(IconsPlugin);
Vue.use(VueNativeWebsocket, 'ws://' + window.location.host + '/ws', {
  reconnection: true,
  reconnectAttempts: 5,
  reconnectionDelay: 3000,
  format: 'json',
})

new Vue({
  render: h => h(App),
}).$mount('#app')
