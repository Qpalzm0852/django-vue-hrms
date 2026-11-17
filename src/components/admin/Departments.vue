<template>
  <div class="biz-page">
    <section class="biz-page__hero">
      <div class="biz-page__hero-copy">
        <p class="biz-page__eyebrow">Organization Structure</p>
        <h1 class="biz-page__title">部门管理</h1>
        <p class="biz-page__description">
          统一维护组织部门与负责人信息，支持按名称检索、新增、编辑和删除，方便后续员工与岗位数据保持一致。
        </p>
        <div class="biz-page__meta">
          <span class="biz-page__badge">部门总数 {{ total }} 个</span>
          <span class="biz-page__badge">当前页 {{ departmentListShow.length }} 个</span>
        </div>
      </div>
      <div class="biz-page__hero-side">
        <div class="biz-page__stat">
          <p class="biz-page__stat-label">已配置负责人</p>
          <p class="biz-page__stat-value">{{ managedCount }}</p>
        </div>
      </div>
    </section>

    <el-card class="biz-page__panel">
      <div class="biz-page__toolbar">
        <div class="biz-page__toolbar-main">
          <h2 class="biz-page__toolbar-title">组织部门列表</h2>
          <p class="biz-page__toolbar-desc">按部门名称检索组织单元，并在右侧直接发起新增操作。</p>
        </div>
        <div class="biz-page__toolbar-actions">
          <el-button type="primary" @click="addDialogVisible = true">添加部门</el-button>
        </div>
      </div>

      <el-form :inline="true" class="biz-page__filters">
        <el-form-item label="部门名称">
          <el-input v-model="searchInput" placeholder="请输入部门名称" clearable style="width: 280px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="getDepartmentList(true)" />
          <el-button type="default" icon="el-icon-refresh-right" @click="getDepartmentList(false)" />
        </el-form-item>
      </el-form>

      <div v-loading="loading" element-loading-text="加载中..." element-loading-spinner="el-icon-loading">
        <el-table :data="departmentListShow" border stripe>
          <el-table-column type="index" label="#" width="60" />
          <el-table-column prop="name" label="部门名称" min-width="160" />
          <el-table-column prop="manager_name" label="部门经理" min-width="120">
            <template slot-scope="scope">
              <span v-if="scope.row.manager_name">{{ scope.row.manager_name }}</span>
              <span v-else class="status-muted">未配置</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" min-width="180" />
          <el-table-column label="操作" width="130" align="center">
            <template slot-scope="scope">
              <el-button type="primary" icon="el-icon-edit" size="mini" @click="showEditDialog(scope.row.id)" />
              <el-button type="danger" icon="el-icon-delete" size="mini" @click="deleteDepartment(scope.row.id)" />
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-if="!loading && !departmentListShow.length" class="biz-page__table-empty">
        <p class="biz-page__table-empty-title">当前没有部门记录</p>
        <p class="biz-page__table-empty-desc">可以清空筛选重新查询，或点击右上角按钮新增部门。</p>
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

    <el-dialog title="添加部门" :visible.sync="addDialogVisible" width="50%" @close="addDialogClosed">
      <el-form ref="addFormRef" :model="addForm" :rules="addFormRules" label-width="100px">
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="addForm.name" placeholder="请输入部门名称" clearable />
        </el-form-item>
        <el-form-item label="部门经理" prop="manager">
          <el-select v-model="addForm.manager" placeholder="请选择部门经理" style="width: 100%" clearable>
            <el-option v-for="item in managerList" :key="item.user_id" :label="item.name" :value="item.user_id" />
          </el-select>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addDepartment">确定</el-button>
      </span>
    </el-dialog>

    <el-dialog title="修改部门信息" :visible.sync="editDialogVisible" width="50%" @close="editDialogClosed">
      <el-form ref="editFormRef" :model="editForm" :rules="editFormRules" label-width="100px">
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入部门名称" clearable />
        </el-form-item>
        <el-form-item label="部门经理" prop="manager">
          <el-select v-model="editForm.manager" placeholder="请选择部门经理" style="width: 100%" clearable>
            <el-option v-for="item in managerList" :key="item.user_id" :label="item.name" :value="item.user_id" />
          </el-select>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="editDepartment">确定</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { getErrorMessage } from '@/utils/errorHandler'

export default {
  computed: {
    managedCount() {
      return this.departmentList.filter((item) => item && item.manager_name).length
    },
  },
  data() {
    return {
      searchInput: '',
      departmentList: [],
      departmentListShow: [],
      managerList: [],
      total: 0,
      currentPage: 1,
      pageSize: 10,
      loading: false,
      addDialogVisible: false,
      addForm: {
        name: '',
        manager: '',
      },
      addFormRules: {
        name: [
          { required: true, message: '请输入部门名称', trigger: 'blur' },
          { min: 2, max: 100, message: '部门名称长度应为 2-100 个字符', trigger: 'blur' },
        ],
      },
      editDialogVisible: false,
      editForm: {
        id: '',
        name: '',
        manager: '',
      },
      editFormRules: {
        name: [
          { required: true, message: '请输入部门名称', trigger: 'blur' },
          { min: 2, max: 100, message: '部门名称长度应为 2-100 个字符', trigger: 'blur' },
        ],
      },
    }
  },
  created() {
    this.getManagerList()
    this.getDepartmentList(false)
  },
  methods: {
    refreshPageData() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.departmentListShow = this.departmentList.slice(start, end)
    },
    async getManagerList() {
      try {
        const { data: res } = await this.$http.get('api/employees/')
        if (Array.isArray(res)) {
          this.managerList = res.filter((item) => ['ADMIN', 'HR', 'MANAGER'].includes(item.role))
        }
      } catch (error) {
        console.error('获取管理人员列表失败:', error)
      }
    },
    async getDepartmentList(search = false) {
      this.loading = true
      try {
        const { data: res } = await this.$http.get('api/departments/')
        if (!Array.isArray(res)) {
          this.$message.error('获取部门列表失败')
          return
        }

        let list = res
        if (search && this.searchInput) {
          list = res.filter((item) => item.name && item.name.includes(this.searchInput.trim()))
        }

        this.departmentList = list
        this.total = list.length
        this.currentPage = 1
        this.refreshPageData()
      } catch (error) {
        console.error('获取部门列表失败:', error)
        this.$message.error(getErrorMessage(error, '获取部门列表失败'))
      } finally {
        this.loading = false
      }
    },
    addDialogClosed() {
      this.$refs.addFormRef && this.$refs.addFormRef.resetFields()
    },
    addDepartment() {
      this.$refs.addFormRef.validate(async (valid) => {
        if (!valid) return
        try {
          await this.$http.post('api/departments/', {
            name: this.addForm.name,
            manager: this.addForm.manager || null,
          })
          this.$message.success('添加部门成功')
          this.addDialogVisible = false
          this.getDepartmentList(false)
        } catch (error) {
          console.error('添加部门失败:', error)
          this.$message.error(getErrorMessage(error, '添加部门失败'))
        }
      })
    },
    async showEditDialog(id) {
      this.editDialogVisible = true
      try {
        const { data: res } = await this.$http.get(`api/departments/${id}/`)
        this.editForm.id = res.id
        this.editForm.name = res.name
        this.editForm.manager = res.manager || ''
      } catch (error) {
        console.error('获取部门信息失败:', error)
        this.$message.error(getErrorMessage(error, '获取部门信息失败'))
        this.editDialogVisible = false
      }
    },
    editDialogClosed() {
      this.$refs.editFormRef && this.$refs.editFormRef.resetFields()
    },
    editDepartment() {
      this.$refs.editFormRef.validate(async (valid) => {
        if (!valid) return
        try {
          await this.$http.patch(`api/departments/${this.editForm.id}/`, {
            name: this.editForm.name,
            manager: this.editForm.manager || null,
          })
          this.$message.success('更新部门信息成功')
          this.editDialogVisible = false
          this.getDepartmentList(false)
        } catch (error) {
          console.error('修改部门失败:', error)
          this.$message.error(getErrorMessage(error, '修改部门失败'))
        }
      })
    },
    deleteDepartment(id) {
      this.$confirm('此操作将永久删除该部门，是否继续？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
        .then(async () => {
          try {
            await this.$http.delete(`api/departments/${id}/`)
            this.$message.success('删除部门成功')
            this.getDepartmentList(false)
          } catch (error) {
            console.error('删除部门失败:', error)
            this.$message.error(getErrorMessage(error, '删除部门失败'))
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
.status-muted {
  color: #909399;
}
</style>
