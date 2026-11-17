<template>
  <div class="biz-page">
    <el-breadcrumb separator-class="el-icon-arrow-right">
      <el-breadcrumb-item :to="{ path: '/admin/home' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item>员工管理</el-breadcrumb-item>
      <el-breadcrumb-item>管理员</el-breadcrumb-item>
    </el-breadcrumb>

    <section class="biz-page__hero">
      <div class="biz-page__hero-content">
        <span class="biz-page__eyebrow">Admin Directory</span>
        <h1>管理员管理</h1>
        <p>集中维护管理员账号、部门归属与在职状态，确保后台角色分配清晰可控。</p>
        <div class="biz-page__badges">
          <span class="biz-page__badge">管理员 {{ total }}</span>
          <span class="biz-page__badge">当前页 {{ adminListShow.length }}</span>
          <span class="biz-page__badge">在职 {{ onboardCount }}</span>
        </div>
      </div>
      <div class="biz-page__hero-stats">
        <article v-for="item in summaryCards" :key="item.label" class="biz-page__stat-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <small>{{ item.helper }}</small>
        </article>
      </div>
    </section>

    <el-card class="biz-page__panel" shadow="never">
      <div class="biz-page__toolbar">
        <div class="biz-page__toolbar-copy">
          <h2>管理员列表</h2>
          <p>支持按工号或姓名快速筛选，当前共 {{ total }} 位管理员。</p>
        </div>
        <div class="biz-page__toolbar-actions">
          <el-button type="primary" icon="el-icon-plus" @click="showAddDialog">添加管理员</el-button>
        </div>
      </div>

      <div class="biz-page__filters">
        <el-input v-model="keyword" class="search-input" :placeholder="'请输入' + searchFieldLabel" clearable>
          <el-select slot="prepend" v-model="selectedField" class="select" placeholder="筛选字段">
            <el-option v-for="item in fieldOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-button slot="append" class="append-btn" icon="el-icon-search" @click="getAdminList(true)" />
          <el-button slot="append" class="append-btn" icon="el-icon-refresh-right" @click="getAdminList(false)" />
        </el-input>
      </div>

      <div v-loading="loading" element-loading-text="加载中..." element-loading-spinner="el-icon-loading">
        <el-table class="data-table" :data="adminListShow" border stripe>
          <el-table-column type="index" label="#" width="58" align="center" />
          <el-table-column prop="user_id" label="工号" min-width="120" />
          <el-table-column prop="user_name" label="姓名" min-width="120" />
          <el-table-column prop="department_name" label="部门" min-width="140">
            <template slot-scope="scope">
              <span>{{ scope.row.department_name || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" min-width="110" align="center">
            <template slot-scope="scope">
              <el-tag size="mini" effect="dark" :type="getStatusTagType(scope.row.status)">
                {{ getStatusLabel(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="124" align="center" fixed="right">
            <template slot-scope="scope">
              <el-button
                class="row-action-btn"
                type="primary"
                icon="el-icon-edit"
                size="mini"
                @click="showEditDialog(scope.row.user_id)"
              />
              <el-button
                class="row-action-btn"
                type="danger"
                icon="el-icon-delete"
                size="mini"
                @click="deleteAdmin(scope.row.user_id)"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-if="!loading && adminListShow.length === 0" class="biz-page__table-empty">
        <i class="el-icon-user-solid" />
        <strong>当前没有匹配的管理员</strong>
        <span>可以切换筛选字段后重新查询，或直接添加新的管理员账号。</span>
      </div>

      <el-pagination
        class="biz-page__pagination"
        :current-page="currentPage"
        :page-sizes="[10, 15, 20, 30]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>

    <el-dialog title="添加管理员" :visible.sync="addDialogVisible" width="56%" @close="addDialogClosed">
      <el-form ref="addFormRef" :model="addForm" :rules="addFormRules" label-width="92px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="工号" prop="user_id">
              <el-input v-model="addForm.user_id" placeholder="请输入工号" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名" prop="user_name">
              <el-input v-model="addForm.user_name" placeholder="请输入姓名" clearable />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="密码" prop="password">
              <el-input v-model="addForm.password" placeholder="请输入登录密码" show-password clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="部门" prop="department">
              <el-select v-model="addForm.department" placeholder="请选择部门" style="width: 100%">
                <el-option v-for="item in departmentList" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <span slot="footer" class="dialog-footer">
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addAdmin">确定</el-button>
      </span>
    </el-dialog>

    <el-dialog title="编辑管理员" :visible.sync="editDialogVisible" width="48%" @close="editDialogClosed">
      <el-form ref="editFormRef" :model="editForm" :rules="editFormRules" label-width="92px">
        <el-form-item label="工号" prop="user_id">
          <el-input v-model="editForm.user_id" disabled />
        </el-form-item>
        <el-form-item label="姓名" prop="user_name">
          <el-input v-model="editForm.user_name" placeholder="请输入姓名" clearable />
        </el-form-item>
      </el-form>

      <span slot="footer" class="dialog-footer">
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="editAdmin">确定</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { getErrorMessage } from '@/utils/errorHandler'

export default {
  data() {
    return {
      fieldOptions: [
        { value: 'user_id', label: '工号' },
        { value: 'user_name', label: '姓名' },
      ],
      selectedField: 'user_id',
      keyword: '',
      loading: false,
      adminList: [],
      adminListShow: [],
      currentPage: 1,
      pageSize: 15,
      total: 0,
      departmentList: [],
      addDialogVisible: false,
      editDialogVisible: false,
      addForm: {
        user_id: '',
        user_name: '',
        password: '',
        department: null,
      },
      editForm: {
        user_id: '',
        user_name: '',
      },
      addFormRules: {
        user_id: [
          { required: true, message: '请输入工号', trigger: 'blur' },
          { min: 3, max: 20, message: '工号长度应为 3-20 个字符', trigger: 'blur' },
        ],
        user_name: [
          { required: true, message: '请输入姓名', trigger: 'blur' },
          { min: 2, max: 50, message: '姓名长度应为 2-50 个字符', trigger: 'blur' },
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, max: 20, message: '密码长度应为 6-20 个字符', trigger: 'blur' },
        ],
        department: [{ required: true, message: '请选择部门', trigger: 'change' }],
      },
      editFormRules: {
        user_name: [
          { required: true, message: '请输入姓名', trigger: 'blur' },
          { min: 2, max: 50, message: '姓名长度应为 2-50 个字符', trigger: 'blur' },
        ],
      },
    }
  },
  computed: {
    searchFieldLabel() {
      const hit = this.fieldOptions.find((item) => item.value === this.selectedField)
      return hit ? hit.label : '关键词'
    },
    onboardCount() {
      return this.adminList.filter((item) => item.status === 'ONBOARD').length
    },
    summaryCards() {
      return [
        {
          label: '在职管理员',
          value: this.onboardCount,
          helper: '正常可用',
        },
        {
          label: '试用状态',
          value: this.adminList.filter((item) => item.status === 'PROBATION').length,
          helper: '待稳定观察',
        },
        {
          label: '部门覆盖',
          value: new Set(this.adminList.map((item) => item.department_name).filter(Boolean)).size,
          helper: '已配置部门',
        },
      ]
    },
  },
  created() {
    this.getDepartmentList()
    this.getAdminList()
  },
  methods: {
    getStatusLabel(status) {
      const map = {
        ONBOARD: '在职',
        PROBATION: '试用',
        LEAVE: '离职',
        SUSPEND: '停薪留职',
      }
      return map[status] || status || '-'
    },
    getStatusTagType(status) {
      const map = {
        ONBOARD: 'success',
        PROBATION: 'warning',
        LEAVE: 'danger',
        SUSPEND: 'info',
      }
      return map[status] || ''
    },
    refreshPageData() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.adminListShow = this.adminList.slice(start, end)
    },
    async getDepartmentList() {
      try {
        const { data: res } = await this.$http.get('api/departments/')
        if (Array.isArray(res)) {
          this.departmentList = res
          if (!this.addForm.department && res.length > 0) {
            this.addForm.department = res[0].id
          }
        }
      } catch (error) {
        console.error('获取部门列表失败:', error)
      }
    },
    async getAdminList(keepKeyword = true) {
      if (!keepKeyword) {
        this.keyword = ''
      }
      this.loading = true
      try {
        const { data: res } = await this.$http.get('api/employees/')
        if (!Array.isArray(res)) {
          this.$message.error('获取管理员列表失败')
          this.adminList = []
          this.adminListShow = []
          this.total = 0
          return
        }

        let filtered = res.filter((item) => String(item.role || '').toUpperCase() === 'ADMIN')

        const keyword = String(this.keyword || '').trim().toLowerCase()
        if (keyword) {
          if (this.selectedField === 'user_name') {
            filtered = filtered.filter((item) => String(item.user_name || '').toLowerCase().includes(keyword))
          } else {
            filtered = filtered.filter((item) => String(item.user_id || '').toLowerCase().includes(keyword))
          }
        }

        this.adminList = filtered
        this.total = filtered.length
        this.currentPage = 1
        this.refreshPageData()
      } catch (error) {
        console.error('获取管理员列表失败:', error)
        this.$message.error(getErrorMessage(error, '获取管理员列表失败'))
      } finally {
        this.loading = false
      }
    },
    showAddDialog() {
      this.addDialogVisible = true
    },
    addDialogClosed() {
      this.$refs.addFormRef && this.$refs.addFormRef.resetFields()
      if (this.departmentList.length > 0) {
        this.addForm.department = this.departmentList[0].id
      }
    },
    addAdmin() {
      this.$refs.addFormRef.validate(async (valid) => {
        if (!valid) return

        const payload = {
          user_id: this.addForm.user_id,
          name: this.addForm.user_name,
          password: this.addForm.password,
          role: 'ADMIN',
          department: this.addForm.department,
        }

        try {
          await this.$http.post('api/employees/', payload)
          this.$message.success('添加管理员成功')
          this.addDialogVisible = false
          this.getAdminList(true)
        } catch (error) {
          console.error('添加管理员失败:', error)
          this.$message.error(getErrorMessage(error, '添加管理员失败'))
        }
      })
    },
    async showEditDialog(id) {
      this.editDialogVisible = true
      try {
        const { data: res } = await this.$http.get(`api/employees/${id}/`)
        this.editForm.user_id = res.user_id
        this.editForm.user_name = res.user_name || res.name || ''
      } catch (error) {
        console.error('获取管理员信息失败:', error)
        this.$message.error(getErrorMessage(error, '获取管理员信息失败'))
        this.editDialogVisible = false
      }
    },
    editDialogClosed() {
      this.$refs.editFormRef && this.$refs.editFormRef.resetFields()
      this.editForm = {
        user_id: '',
        user_name: '',
      }
    },
    editAdmin() {
      this.$refs.editFormRef.validate(async (valid) => {
        if (!valid) return

        try {
          await this.$http.patch(`api/employees/${this.editForm.user_id}/`, {
            name: this.editForm.user_name,
          })
          this.$message.success('更新管理员信息成功')
          this.editDialogVisible = false
          this.getAdminList(true)
        } catch (error) {
          console.error('更新管理员信息失败:', error)
          this.$message.error(getErrorMessage(error, '更新管理员信息失败'))
        }
      })
    },
    deleteAdmin(id) {
      this.$confirm('此操作将永久删除该管理员，是否继续？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
        .then(async () => {
          try {
            await this.$http.delete(`api/employees/${id}/`)
            this.$message.success('删除管理员成功')
            this.getAdminList(true)
          } catch (error) {
            console.error('删除管理员失败:', error)
            this.$message.error(getErrorMessage(error, '删除管理员失败'))
          }
        })
        .catch(() => {
          this.$message.info('已取消删除')
        })
    },
    handleSizeChange(pageSize) {
      this.pageSize = pageSize
      this.currentPage = 1
      this.refreshPageData()
    },
    handleCurrentChange(currentPage) {
      this.currentPage = currentPage
      this.refreshPageData()
    },
  },
}
</script>

<style lang="less" scoped>
/deep/ .el-breadcrumb {
  margin: 4px 0 10px;
}

/deep/ .el-breadcrumb__inner {
  color: #355d92;
}

.search-input {
  max-width: 520px;
}

.select {
  width: 116px;
}

/deep/ .search-input .el-input-group__prepend,
/deep/ .search-input .el-input-group__append {
  background: rgba(242, 248, 255, 0.95);
  border-color: rgba(20, 78, 157, 0.18);
}

/deep/ .search-input .el-input__inner,
/deep/ .search-input .el-select .el-input__inner {
  border-color: #d5deea;
}

.append-btn {
  color: #2a69b2;
}

.row-action-btn {
  box-shadow: none;
}

/deep/ .el-dialog {
  border-radius: 16px;
  overflow: hidden;
}

/deep/ .el-dialog__header {
  background: #f8fafc;
  border-bottom: 1px solid #e7edf5;
}

/deep/ .el-dialog__body {
  padding: 20px 22px 14px;
}

/deep/ .el-dialog__footer {
  border-top: 1px solid #e7edf5;
  background: #f8fafc;
}

@media (max-width: 768px) {
  .search-input {
    max-width: 100%;
  }

  .row-action-btn + .row-action-btn {
    margin-left: 6px;
  }
}
</style>

