<template>
  <div class="biz-page">
    <section class="biz-page__hero">
      <div class="biz-page__hero-copy">
        <p class="biz-page__eyebrow">Position Library</p>
        <h1 class="biz-page__title">岗位管理</h1>
        <p class="biz-page__description">
          统一维护岗位名称、所属部门、级别代码和类别信息，支持按岗位名称检索、新增、编辑和删除。
        </p>
        <div class="biz-page__meta">
          <span class="biz-page__badge">岗位总数 {{ total }} 个</span>
          <span class="biz-page__badge">当前页 {{ positionListShow.length }} 个</span>
        </div>
      </div>
      <div class="biz-page__hero-side">
        <div class="biz-page__stat">
          <p class="biz-page__stat-label">已归属部门</p>
          <p class="biz-page__stat-value">{{ assignedCount }}</p>
        </div>
      </div>
    </section>

    <el-card class="biz-page__panel">
      <div class="biz-page__toolbar">
        <div class="biz-page__toolbar-main">
          <h2 class="biz-page__toolbar-title">岗位列表</h2>
          <p class="biz-page__toolbar-desc">按岗位名称检索岗位设置，并在右侧直接发起新增操作。</p>
        </div>
        <div class="biz-page__toolbar-actions">
          <el-button type="primary" @click="addDialogVisible = true">添加岗位</el-button>
        </div>
      </div>

      <el-form :inline="true" class="biz-page__filters">
        <el-form-item label="岗位名称">
          <el-input v-model="searchInput" placeholder="请输入岗位名称" clearable style="width: 280px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="getPositionList(true)" />
          <el-button type="default" icon="el-icon-refresh-right" @click="getPositionList(false)" />
        </el-form-item>
      </el-form>

      <div v-loading="loading" element-loading-text="加载中..." element-loading-spinner="el-icon-loading">
        <el-table :data="positionListShow" border stripe>
          <el-table-column type="index" label="#" width="60" />
          <el-table-column prop="name" label="岗位名称" min-width="150" />
          <el-table-column prop="department_name" label="所属部门" min-width="130">
            <template slot-scope="scope">
              <span v-if="scope.row.department_name">{{ scope.row.department_name }}</span>
              <span v-else class="status-muted">未设置</span>
            </template>
          </el-table-column>
          <el-table-column prop="level_code" label="级别代码" min-width="110">
            <template slot-scope="scope">
              <span v-if="scope.row.level_code">{{ scope.row.level_code }}</span>
              <span v-else class="status-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="category" label="类别" min-width="100">
            <template slot-scope="scope">
              <span v-if="scope.row.category">{{ scope.row.category }}</span>
              <span v-else class="status-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" min-width="180" />
          <el-table-column label="操作" width="130" align="center">
            <template slot-scope="scope">
              <el-button type="primary" icon="el-icon-edit" size="mini" @click="showEditDialog(scope.row.id)" />
              <el-button type="danger" icon="el-icon-delete" size="mini" @click="deletePosition(scope.row.id)" />
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-if="!loading && !positionListShow.length" class="biz-page__table-empty">
        <p class="biz-page__table-empty-title">当前没有岗位记录</p>
        <p class="biz-page__table-empty-desc">可以清空筛选重新查询，或点击右上角按钮新增岗位。</p>
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

    <el-dialog title="添加岗位" :visible.sync="addDialogVisible" width="50%" @close="addDialogClosed">
      <el-form ref="addFormRef" :model="addForm" :rules="addFormRules" label-width="100px">
        <el-form-item label="岗位名称" prop="name">
          <el-input v-model="addForm.name" placeholder="请输入岗位名称" clearable />
        </el-form-item>
        <el-form-item label="所属部门" prop="department">
          <el-select v-model="addForm.department" placeholder="请选择部门" style="width: 100%">
            <el-option v-for="item in departmentList" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="级别代码" prop="level_code">
          <el-input v-model="addForm.level_code" placeholder="请输入级别代码（可选）" clearable />
        </el-form-item>
        <el-form-item label="类别" prop="category">
          <el-select v-model="addForm.category" placeholder="请选择类别（可选）" style="width: 100%" clearable>
            <el-option label="技术" value="技术" />
            <el-option label="职能" value="职能" />
            <el-option label="管理" value="管理" />
          </el-select>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addPosition">确定</el-button>
      </span>
    </el-dialog>

    <el-dialog title="修改岗位信息" :visible.sync="editDialogVisible" width="50%" @close="editDialogClosed">
      <el-form ref="editFormRef" :model="editForm" :rules="editFormRules" label-width="100px">
        <el-form-item label="岗位名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入岗位名称" clearable />
        </el-form-item>
        <el-form-item label="所属部门" prop="department">
          <el-select v-model="editForm.department" placeholder="请选择部门" style="width: 100%">
            <el-option v-for="item in departmentList" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="级别代码" prop="level_code">
          <el-input v-model="editForm.level_code" placeholder="请输入级别代码（可选）" clearable />
        </el-form-item>
        <el-form-item label="类别" prop="category">
          <el-select v-model="editForm.category" placeholder="请选择类别（可选）" style="width: 100%" clearable>
            <el-option label="技术" value="技术" />
            <el-option label="职能" value="职能" />
            <el-option label="管理" value="管理" />
          </el-select>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="editPosition">确定</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { getErrorMessage } from '@/utils/errorHandler'

export default {
  computed: {
    assignedCount() {
      return this.positionList.filter((item) => item && item.department_name).length
    },
  },
  data() {
    return {
      searchInput: '',
      positionList: [],
      positionListShow: [],
      departmentList: [],
      total: 0,
      currentPage: 1,
      pageSize: 10,
      loading: false,
      addDialogVisible: false,
      addForm: {
        name: '',
        department: '',
        level_code: '',
        category: '',
      },
      addFormRules: {
        name: [
          { required: true, message: '请输入岗位名称', trigger: 'blur' },
          { min: 2, max: 100, message: '岗位名称长度应为 2-100 个字符', trigger: 'blur' },
        ],
        department: [{ required: true, message: '请选择部门', trigger: 'change' }],
      },
      editDialogVisible: false,
      editForm: {
        id: '',
        name: '',
        department: '',
        level_code: '',
        category: '',
      },
      editFormRules: {
        name: [
          { required: true, message: '请输入岗位名称', trigger: 'blur' },
          { min: 2, max: 100, message: '岗位名称长度应为 2-100 个字符', trigger: 'blur' },
        ],
        department: [{ required: true, message: '请选择部门', trigger: 'change' }],
      },
    }
  },
  created() {
    this.getDepartmentList()
    this.getPositionList(false)
  },
  methods: {
    refreshPageData() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.positionListShow = this.positionList.slice(start, end)
    },
    async getDepartmentList() {
      try {
        const { data: res } = await this.$http.get('api/departments/')
        if (Array.isArray(res)) {
          this.departmentList = res
        }
      } catch (error) {
        console.error('获取部门列表失败:', error)
      }
    },
    async getPositionList(search = false) {
      this.loading = true
      try {
        const { data: res } = await this.$http.get('api/positions/')
        if (!Array.isArray(res)) {
          this.$message.error('获取岗位列表失败')
          return
        }

        let list = res
        if (search && this.searchInput) {
          list = res.filter((item) => item.name && item.name.includes(this.searchInput.trim()))
        }

        this.positionList = list
        this.total = list.length
        this.currentPage = 1
        this.refreshPageData()
      } catch (error) {
        console.error('获取岗位列表失败:', error)
        this.$message.error(getErrorMessage(error, '获取岗位列表失败'))
      } finally {
        this.loading = false
      }
    },
    addDialogClosed() {
      this.$refs.addFormRef && this.$refs.addFormRef.resetFields()
    },
    addPosition() {
      this.$refs.addFormRef.validate(async (valid) => {
        if (!valid) return
        try {
          await this.$http.post('api/positions/', {
            name: this.addForm.name,
            department: this.addForm.department,
            level_code: this.addForm.level_code || null,
            category: this.addForm.category || null,
          })
          this.$message.success('添加岗位成功')
          this.addDialogVisible = false
          this.getPositionList(false)
        } catch (error) {
          console.error('添加岗位失败:', error)
          this.$message.error(getErrorMessage(error, '添加岗位失败'))
        }
      })
    },
    async showEditDialog(id) {
      this.editDialogVisible = true
      try {
        const { data: res } = await this.$http.get(`api/positions/${id}/`)
        this.editForm.id = res.id
        this.editForm.name = res.name
        this.editForm.department = res.department
        this.editForm.level_code = res.level_code || ''
        this.editForm.category = res.category || ''
      } catch (error) {
        console.error('获取岗位信息失败:', error)
        this.$message.error(getErrorMessage(error, '获取岗位信息失败'))
        this.editDialogVisible = false
      }
    },
    editDialogClosed() {
      this.$refs.editFormRef && this.$refs.editFormRef.resetFields()
    },
    editPosition() {
      this.$refs.editFormRef.validate(async (valid) => {
        if (!valid) return
        try {
          await this.$http.patch(`api/positions/${this.editForm.id}/`, {
            name: this.editForm.name,
            department: this.editForm.department,
            level_code: this.editForm.level_code || null,
            category: this.editForm.category || null,
          })
          this.$message.success('更新岗位信息成功')
          this.editDialogVisible = false
          this.getPositionList(false)
        } catch (error) {
          console.error('修改岗位失败:', error)
          this.$message.error(getErrorMessage(error, '修改岗位失败'))
        }
      })
    },
    deletePosition(id) {
      this.$confirm('此操作将永久删除该岗位，是否继续？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
        .then(async () => {
          try {
            await this.$http.delete(`api/positions/${id}/`)
            this.$message.success('删除岗位成功')
            this.getPositionList(false)
          } catch (error) {
            console.error('删除岗位失败:', error)
            this.$message.error(getErrorMessage(error, '删除岗位失败'))
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
