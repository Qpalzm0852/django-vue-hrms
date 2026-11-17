import Vue from 'vue'
import { 
  Button, Input, Message, Form, FormItem, 
  Container, Header, Aside, Main,
  Menu, Submenu, MenuItem, Breadcrumb, BreadcrumbItem,
  Card, Row, Col, Table, TableColumn, Tooltip, Pagination, 
  Select, Option, Dialog, MessageBox, Upload, 
  Checkbox, DatePicker, Divider, InputNumber, Tag,
  Tabs, TabPane, Alert, Badge, Loading
} from 'element-ui'

Vue.use(Button)
Vue.use(Input)
Vue.use(Form)
Vue.use(FormItem)
Vue.use(Container)
Vue.use(Header)
Vue.use(Aside)
Vue.use(Main)
Vue.use(Menu)
Vue.use(Submenu)
Vue.use(MenuItem)
Vue.use(Breadcrumb)
Vue.use(BreadcrumbItem)
Vue.use(Card)
Vue.use(Row)
Vue.use(Col)
Vue.use(Table)
Vue.use(TableColumn)
Vue.use(Tooltip)
Vue.use(Pagination)
Vue.use(Select)
Vue.use(Option)
Vue.use(Dialog)
Vue.use(Upload)
Vue.use(Checkbox)
Vue.use(DatePicker)
Vue.use(Divider)
Vue.use(InputNumber)
Vue.use(Tag)
Vue.use(Tabs)
Vue.use(TabPane)
Vue.use(Alert)
Vue.use(Badge)
// 全局注册 loading 指令和服务，支持 v-loading
Vue.use(Loading.directive)
Vue.prototype.$loading = Loading.service
Vue.prototype.$message = Message
Vue.prototype.$confirm = MessageBox.confirm
