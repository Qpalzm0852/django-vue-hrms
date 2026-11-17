<template>
  <div class="biz-page recruitment-page">
    <el-breadcrumb separator-class="el-icon-arrow-right">
      <el-breadcrumb-item :to="{ path: '/admin/home' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item>招聘管理</el-breadcrumb-item>
      <el-breadcrumb-item>招聘总览</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card class="hero-card biz-page__hero biz-page__panel" shadow="never">
      <div class="hero-main biz-page__toolbar">
        <div>
          <h2>人才招聘中心</h2>
          <p>统一管理招聘需求、候选人简历与面试流程，支持快速筛选与状态追踪。</p>
        </div>
        <div class="hero-tags">
          <el-tag type="success" effect="dark">需求 {{ requirementTotal }}</el-tag>
          <el-tag type="warning" effect="dark">简历 {{ resumeTotal }}</el-tag>
          <el-tag type="primary" effect="dark">面试 {{ interviewTotal }}</el-tag>
        </div>
      </div>

      <div class="summary-grid biz-page__hero-stats">
        <div class="summary-item" v-for="item in summaryCards" :key="item.key">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>
    </el-card>

    <el-tabs v-model="activeTab" type="border-card" class="recruitment-tabs">
      <el-tab-pane label="招聘需求" name="requirements">
        <div class="tab-content">
          <el-row :gutter="16" class="toolbar-row">
            <el-col :xs="24" :sm="12" :md="6">
              <el-input
                v-model="requirementSearch"
                placeholder="搜索职位名称"
                clearable
                @clear="getRequirementList"
                @keyup.enter.native="getRequirementList"
              >
                <el-button slot="append" icon="el-icon-search" @click="getRequirementList" />
              </el-input>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <el-select v-model="requirementStatusFilter" placeholder="状态筛选" clearable @change="getRequirementList" style="width: 100%">
                <el-option label="草稿" value="DRAFT" />
                <el-option label="已发布" value="PUBLISHED" />
                <el-option label="已关闭" value="CLOSED" />
                <el-option label="已取消" value="CANCELLED" />
              </el-select>
            </el-col>
            <el-col :xs="24" :sm="24" :md="12" class="toolbar-actions">
              <el-button type="primary" icon="el-icon-plus" @click="showAddRequirementDialog">发布需求</el-button>
            </el-col>
          </el-row>

          <el-table :data="requirementListShow" border stripe class="data-table">
            <el-table-column type="index" label="序号" width="64" />
            <el-table-column prop="title" label="职位名称" min-width="160" />
            <el-table-column prop="department_name" label="部门" width="120" />
            <el-table-column prop="position_name" label="岗位" width="120">
              <template slot-scope="scope">{{ scope.row.position_name || '-' }}</template>
            </el-table-column>
            <el-table-column prop="number" label="招聘人数" width="100" />
            <el-table-column prop="status" label="状态" width="100">
              <template slot-scope="scope">
                <el-tag :type="getStatusTagType(scope.row.status)">{{ getStatusText(scope.row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="publisher_name" label="发布人" width="100">
              <template slot-scope="scope">{{ scope.row.publisher_name || '-' }}</template>
            </el-table-column>
            <el-table-column prop="publish_time" label="发布时间" width="170">
              <template slot-scope="scope">{{ scope.row.publish_time || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="220" fixed="right">
              <template slot-scope="scope">
                <el-button type="primary" size="mini" @click="showEditRequirementDialog(scope.row)">编辑</el-button>
                <el-button
                  v-if="scope.row.status === 'DRAFT'"
                  type="success"
                  size="mini"
                  @click="publishRequirement(scope.row)"
                >发布</el-button>
                <el-button
                  v-if="scope.row.status === 'PUBLISHED'"
                  type="warning"
                  size="mini"
                  @click="closeRequirement(scope.row)"
                >关闭</el-button>
                <el-button type="danger" size="mini" @click="deleteRequirement(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            class="pagination"
            @size-change="handleRequirementSizeChange"
            @current-change="handleRequirementCurrentChange"
            :current-page="requirementCurrentPage"
            :page-sizes="[10, 15, 20, 30]"
            :page-size="requirementPageSize"
            layout="total, sizes, prev, pager, next, jumper"
            :total="requirementTotal"
          />
        </div>
      </el-tab-pane>
      <el-tab-pane label="简历管理" name="resumes">
        <div class="tab-content">
          <el-row :gutter="16" class="toolbar-row">
            <el-col :xs="24" :sm="12" :md="6">
              <el-input
                v-model="resumeSearch"
                placeholder="搜索姓名或手机号"
                clearable
                @clear="getResumeList"
                @keyup.enter.native="getResumeList"
              >
                <el-button slot="append" icon="el-icon-search" @click="getResumeList" />
              </el-input>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <el-select v-model="resumeStatusFilter" placeholder="状态筛选" clearable @change="getResumeList" style="width: 100%">
                <el-option label="新简历" value="NEW" />
                <el-option label="筛选中" value="SCREENING" />
                <el-option label="面试中" value="INTERVIEW" />
                <el-option label="待录用" value="OFFER" />
                <el-option label="已录用" value="HIRED" />
                <el-option label="已拒绝" value="REJECTED" />
              </el-select>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <el-select v-model="selectedRequirementId" placeholder="选择招聘需求" clearable @change="getResumeList" style="width: 100%">
                <el-option v-for="req in requirementList" :key="req.id" :label="req.title" :value="req.id" />
              </el-select>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6" class="toolbar-actions">
              <el-button type="primary" icon="el-icon-plus" @click="showAddResumeDialog">添加简历</el-button>
            </el-col>
          </el-row>

          <el-table :data="resumeListShow" border stripe class="data-table">
            <el-table-column type="index" label="序号" width="64" />
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column prop="phone" label="手机号" width="130" />
            <el-table-column prop="email" label="邮箱" width="180">
              <template slot-scope="scope">{{ scope.row.email || '-' }}</template>
            </el-table-column>
            <el-table-column prop="recruitment_title" label="应聘职位" min-width="150" />
            <el-table-column prop="education" label="学历" width="100">
              <template slot-scope="scope">{{ scope.row.education || '-' }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template slot-scope="scope">
                <el-tag :type="getResumeStatusTagType(scope.row.status)">{{ getResumeStatusText(scope.row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="260" fixed="right">
              <template slot-scope="scope">
                <el-button type="primary" size="mini" @click="showResumeDetail(scope.row)">详情</el-button>
                <el-button type="success" size="mini" @click="showAddInterviewDialog(scope.row)">安排面试</el-button>
                <el-button type="warning" size="mini" @click="showEditResumeDialog(scope.row)">编辑</el-button>
                <el-button type="danger" size="mini" @click="deleteResume(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            class="pagination"
            @size-change="handleResumeSizeChange"
            @current-change="handleResumeCurrentChange"
            :current-page="resumeCurrentPage"
            :page-sizes="[10, 15, 20, 30]"
            :page-size="resumePageSize"
            layout="total, sizes, prev, pager, next, jumper"
            :total="resumeTotal"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane label="面试管理" name="interviews">
        <div class="tab-content">
          <el-row :gutter="16" class="toolbar-row">
            <el-col :xs="24" :sm="12" :md="6">
              <el-input
                v-model="interviewSearch"
                placeholder="搜索姓名或手机号"
                clearable
                @clear="getInterviewList"
                @keyup.enter.native="getInterviewList"
              >
                <el-button slot="append" icon="el-icon-search" @click="getInterviewList" />
              </el-input>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <el-select v-model="interviewStatusFilter" placeholder="状态筛选" clearable @change="getInterviewList" style="width: 100%">
                <el-option label="已安排" value="SCHEDULED" />
                <el-option label="进行中" value="IN_PROGRESS" />
                <el-option label="已完成" value="COMPLETED" />
                <el-option label="已取消" value="CANCELLED" />
              </el-select>
            </el-col>
            <el-col :xs="24" :sm="24" :md="12" class="toolbar-actions">
              <el-button type="primary" icon="el-icon-plus" @click="showAddInterviewDialog(null)">安排面试</el-button>
            </el-col>
          </el-row>

          <el-table :data="interviewListShow" border stripe class="data-table">
            <el-table-column type="index" label="序号" width="64" />
            <el-table-column prop="resume_name" label="姓名" width="100" />
            <el-table-column prop="resume_phone" label="手机号" width="130" />
            <el-table-column prop="round" label="轮次" width="80" />
            <el-table-column prop="interview_type" label="面试类型" width="120">
              <template slot-scope="scope">{{ scope.row.interview_type || '-' }}</template>
            </el-table-column>
            <el-table-column prop="scheduled_time" label="面试时间" width="170" />
            <el-table-column prop="location" label="面试地点" min-width="150">
              <template slot-scope="scope">{{ scope.row.location || '-' }}</template>
            </el-table-column>
            <el-table-column label="面试官" min-width="150">
              <template slot-scope="scope">
                <span v-if="scope.row.interviewers_info && scope.row.interviewers_info.length > 0">
                  {{ scope.row.interviewers_info.map(i => i.name).join('、') }}
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template slot-scope="scope">
                <el-tag :type="getInterviewStatusTagType(scope.row.status)">{{ getInterviewStatusText(scope.row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="220" fixed="right">
              <template slot-scope="scope">
                <el-button type="primary" size="mini" @click="showEditInterviewDialog(scope.row)">编辑</el-button>
                <el-button
                  v-if="scope.row.status === 'SCHEDULED'"
                  type="success"
                  size="mini"
                  @click="showCompleteInterviewDialog(scope.row)"
                >完成</el-button>
                <el-button type="danger" size="mini" @click="deleteInterview(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            class="pagination"
            @size-change="handleInterviewSizeChange"
            @current-change="handleInterviewCurrentChange"
            :current-page="interviewCurrentPage"
            :page-sizes="[10, 15, 20, 30]"
            :page-size="interviewPageSize"
            layout="total, sizes, prev, pager, next, jumper"
            :total="interviewTotal"
          />
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog :title="requirementDialogTitle" :visible.sync="requirementDialogVisible" width="60%" @close="requirementDialogClosed">
      <el-form ref="requirementForm" :model="requirementForm" :rules="requirementFormRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="职位名称" prop="title">
              <el-input v-model="requirementForm.title" placeholder="请输入职位名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="部门" prop="department">
              <el-select v-model="requirementForm.department" placeholder="请选择部门" style="width: 100%">
                <el-option v-for="dept in departmentList" :key="dept.name" :label="dept.name" :value="dept.name" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="岗位" prop="position">
              <el-select v-model="requirementForm.position" placeholder="请选择岗位" style="width: 100%" filterable>
                <el-option v-for="pos in filteredPositionList" :key="pos.name" :label="pos.name" :value="pos.name" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="招聘人数" prop="number">
              <el-input-number v-model="requirementForm.number" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最低薪资">
              <el-input-number v-model="requirementForm.salary_min" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最高薪资">
              <el-input-number v-model="requirementForm.salary_max" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="截止日期">
          <el-date-picker v-model="requirementForm.deadline" type="date" placeholder="选择截止日期" style="width: 100%" value-format="yyyy-MM-dd" />
        </el-form-item>
        <el-form-item label="职位描述">
          <el-input v-model="requirementForm.description" type="textarea" :rows="4" placeholder="请输入职位描述" />
        </el-form-item>
        <el-form-item label="任职要求">
          <el-input v-model="requirementForm.requirements" type="textarea" :rows="4" placeholder="请输入任职要求" />
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="requirementDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRequirement">确定</el-button>
      </span>
    </el-dialog>

    <el-dialog :title="resumeDialogTitle" :visible.sync="resumeDialogVisible" width="60%" @close="resumeDialogClosed">
      <el-form ref="resumeForm" :model="resumeForm" :rules="resumeFormRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="招聘需求" prop="recruitment"><el-select v-model="resumeForm.recruitment" placeholder="请选择招聘需求" style="width: 100%"><el-option v-for="req in requirementList" :key="req.id" :label="req.title" :value="req.id" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="姓名" prop="name"><el-input v-model="resumeForm.name" placeholder="请输入姓名" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="手机号" prop="phone"><el-input v-model="resumeForm.phone" placeholder="请输入手机号" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="邮箱"><el-input v-model="resumeForm.email" placeholder="请输入邮箱" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="性别"><el-select v-model="resumeForm.gender" placeholder="请选择性别" style="width: 100%"><el-option label="男" value="男" /><el-option label="女" value="女" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="学历"><el-input v-model="resumeForm.education" placeholder="请输入学历" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="工作经历"><el-input v-model="resumeForm.work_experience" type="textarea" :rows="3" placeholder="请输入工作经历" /></el-form-item>
        <el-form-item label="技能特长"><el-input v-model="resumeForm.skills" type="textarea" :rows="3" placeholder="请输入技能特长" /></el-form-item>
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="简历来源"><el-input v-model="resumeForm.source" placeholder="请输入简历来源" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="状态"><el-select v-model="resumeForm.status" placeholder="请选择状态" style="width: 100%"><el-option label="新简历" value="NEW" /><el-option label="筛选中" value="SCREENING" /><el-option label="面试中" value="INTERVIEW" /><el-option label="待录用" value="OFFER" /><el-option label="已录用" value="HIRED" /><el-option label="已拒绝" value="REJECTED" /></el-select></el-form-item></el-col>
        </el-row>
        <el-form-item label="备注"><el-input v-model="resumeForm.note" type="textarea" :rows="3" placeholder="请输入备注" /></el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer"><el-button @click="resumeDialogVisible = false">取消</el-button><el-button type="primary" @click="saveResume">确定</el-button></span>
    </el-dialog>

    <el-dialog :title="interviewDialogTitle" :visible.sync="interviewDialogVisible" width="60%" @close="interviewDialogClosed">
      <el-form ref="interviewForm" :model="interviewForm" :rules="interviewFormRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="简历" prop="resume"><el-select v-model="interviewForm.resume" placeholder="请选择简历" style="width: 100%" filterable><el-option v-for="resume in resumeList" :key="resume.id" :label="resume.name + ' - ' + resume.recruitment_title" :value="resume.id" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="面试轮次"><el-input-number v-model="interviewForm.round" :min="1" style="width: 100%" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="面试类型"><el-input v-model="interviewForm.interview_type" placeholder="如：初试、复试、终试" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="面试时间" prop="scheduled_time"><el-date-picker v-model="interviewForm.scheduled_time" type="datetime" placeholder="选择面试时间" style="width: 100%" value-format="yyyy-MM-dd HH:mm:ss" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="面试地点"><el-input v-model="interviewForm.location" placeholder="请输入面试地点" /></el-form-item>
        <el-form-item label="面试官"><el-select v-model="interviewForm.interviewer_ids" multiple placeholder="请选择面试官" style="width: 100%"><el-option v-for="emp in employeeList" :key="emp.user_id" :label="emp.user_name + ' (' + emp.user_id + ')'" :value="emp.user_id" /></el-select></el-form-item>
        <el-form-item label="状态"><el-select v-model="interviewForm.status" placeholder="请选择状态" style="width: 100%"><el-option label="已安排" value="SCHEDULED" /><el-option label="进行中" value="IN_PROGRESS" /><el-option label="已完成" value="COMPLETED" /><el-option label="已取消" value="CANCELLED" /></el-select></el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer"><el-button @click="interviewDialogVisible = false">取消</el-button><el-button type="primary" @click="saveInterview">确定</el-button></span>
    </el-dialog>

    <el-dialog title="完成面试" :visible.sync="completeInterviewDialogVisible" width="50%" @close="completeInterviewDialogClosed">
      <el-form ref="completeInterviewForm" :model="completeInterviewForm" :rules="completeInterviewFormRules" label-width="100px">
        <el-form-item label="面试结果" prop="result"><el-select v-model="completeInterviewForm.result" placeholder="请选择面试结果" style="width: 100%"><el-option label="通过" value="PASS" /><el-option label="不通过" value="FAIL" /><el-option label="待定" value="PENDING" /></el-select></el-form-item>
        <el-form-item label="评分"><el-input-number v-model="completeInterviewForm.score" :min="0" :max="100" :precision="2" style="width: 100%" /></el-form-item>
        <el-form-item label="面试评价"><el-input v-model="completeInterviewForm.comment" type="textarea" :rows="4" placeholder="请输入面试评价" /></el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer"><el-button @click="completeInterviewDialogVisible = false">取消</el-button><el-button type="primary" @click="completeInterview">确定</el-button></span>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'Recruitment',
  data() {
    return {
      activeTab: 'requirements',
      requirementList: [], requirementListShow: [], requirementCurrentPage: 1, requirementPageSize: 15, requirementTotal: 0,
      requirementSearch: '', requirementStatusFilter: '', requirementDialogVisible: false, requirementDialogTitle: '发布需求',
      requirementForm: { id: null, title: '', department: '', position: '', number: 1, salary_min: null, salary_max: null, deadline: null, description: '', requirements: '' },
      requirementFormRules: {
        title: [{ required: true, message: '请输入职位名称', trigger: 'blur' }],
        department: [{ required: true, message: '请选择部门', trigger: 'change' }],
        number: [{ required: true, message: '请输入招聘人数', trigger: 'blur' }],
      },
      resumeList: [], resumeListShow: [], resumeCurrentPage: 1, resumePageSize: 15, resumeTotal: 0,
      resumeSearch: '', resumeStatusFilter: '', selectedRequirementId: null, resumeDialogVisible: false, resumeDialogTitle: '添加简历',
      resumeForm: { id: null, recruitment: '', name: '', phone: '', email: '', gender: '', education: '', work_experience: '', skills: '', source: '', status: 'NEW', note: '' },
      resumeFormRules: {
        recruitment: [{ required: true, message: '请选择招聘需求', trigger: 'change' }],
        name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
        phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
      },
      interviewList: [], interviewListShow: [], interviewCurrentPage: 1, interviewPageSize: 15, interviewTotal: 0,
      interviewSearch: '', interviewStatusFilter: '', interviewDialogVisible: false, interviewDialogTitle: '安排面试',
      interviewForm: { id: null, resume: '', round: 1, interview_type: '', scheduled_time: '', location: '', interviewer_ids: [], status: 'SCHEDULED' },
      interviewFormRules: {
        resume: [{ required: true, message: '请选择简历', trigger: 'change' }],
        scheduled_time: [{ required: true, message: '请选择面试时间', trigger: 'change' }],
      },
      completeInterviewDialogVisible: false,
      completeInterviewForm: { id: null, result: '', score: null, comment: '' },
      completeInterviewFormRules: { result: [{ required: true, message: '请选择面试结果', trigger: 'change' }] },
      departmentList: [], positionList: [], employeeList: [],
    }
  },
  computed: {
    filteredPositionList() { if (!this.requirementForm.department) return []; return this.positionList.filter(pos => pos.department_name === this.requirementForm.department) },
    summaryCards() {
      return [
        { key: 'published', label: '进行中需求', value: this.requirementList.filter(item => item.status === 'PUBLISHED').length },
        { key: 'screening', label: '筛选中简历', value: this.resumeList.filter(item => item.status === 'SCREENING').length },
        { key: 'interviewing', label: '面试中候选人', value: this.resumeList.filter(item => item.status === 'INTERVIEW').length },
        { key: 'allInterviews', label: '面试总场次', value: this.interviewTotal },
      ]
    },
  },
  mounted() { this.getDepartmentList(); this.getPositionList(); this.getRequirementList(); this.getEmployeeList(); if (this.activeTab === 'resumes') this.getResumeList() },
  watch: {
    activeTab(newTab) {
      if (newTab === 'resumes') { this.resumeCurrentPage = 1; this.getResumeList() }
      else if (newTab === 'interviews') { this.interviewCurrentPage = 1; this.getInterviewList() }
    },
  },
  methods: {
    getStatusText(status) { const map = { DRAFT: '草稿', PUBLISHED: '已发布', CLOSED: '已关闭', CANCELLED: '已取消' }; return map[status] || status },
    getStatusTagType(status) { const map = { DRAFT: 'info', PUBLISHED: 'success', CLOSED: 'warning', CANCELLED: 'danger' }; return map[status] || '' },
    getResumeStatusText(status) { const map = { NEW: '新简历', SCREENING: '筛选中', INTERVIEW: '面试中', OFFER: '待录用', HIRED: '已录用', REJECTED: '已拒绝' }; return map[status] || status },
    getResumeStatusTagType(status) { const map = { NEW: 'info', SCREENING: 'warning', INTERVIEW: 'primary', OFFER: 'success', HIRED: 'success', REJECTED: 'danger' }; return map[status] || '' },
    getInterviewStatusText(status) { const map = { SCHEDULED: '已安排', IN_PROGRESS: '进行中', COMPLETED: '已完成', CANCELLED: '已取消' }; return map[status] || status },
    getInterviewStatusTagType(status) { const map = { SCHEDULED: 'info', IN_PROGRESS: 'warning', COMPLETED: 'success', CANCELLED: 'danger' }; return map[status] || '' },

    async getDepartmentList() { try { const { data: res } = await this.$http.get('/api/departments/'); this.departmentList = res || [] } catch (error) { console.error('获取部门列表失败:', error) } },
    async getPositionList() { try { const { data: res } = await this.$http.get('/api/positions/'); this.positionList = res || [] } catch (error) { console.error('获取岗位列表失败:', error) } },
    async getEmployeeList() { try { const { data: res } = await this.$http.get('/api/employees/'); this.employeeList = res || [] } catch (error) { console.error('获取员工列表失败:', error) } },

    async getRequirementList() {
      try {
        const { data: res } = await this.$http.get('api/recruitment-requirements/')
        let list = Array.isArray(res) ? res : []
        if (this.requirementSearch) list = list.filter(item => item.title && item.title.includes(this.requirementSearch))
        if (this.requirementStatusFilter) list = list.filter(item => item.status === this.requirementStatusFilter)
        this.requirementList = list
        this.requirementTotal = list.length
        this.updateRequirementListShow()
      } catch (error) {
        console.error('获取招聘需求列表失败:', error)
        this.$message.error('获取招聘需求列表失败')
        this.requirementList = []
        this.requirementListShow = []
        this.requirementTotal = 0
      }
    },
    showAddRequirementDialog() {
      this.requirementDialogTitle = '发布需求'
      this.requirementForm = { id: null, title: '', department: '', position: '', number: 1, salary_min: null, salary_max: null, deadline: null, description: '', requirements: '' }
      this.requirementDialogVisible = true
    },
    showEditRequirementDialog(row) {
      this.requirementDialogTitle = '编辑需求'
      this.requirementForm = {
        id: row.id, title: row.title, department: row.department_name, position: row.position_name, number: row.number,
        salary_min: row.salary_min, salary_max: row.salary_max, deadline: row.deadline, description: row.description, requirements: row.requirements,
      }
      this.requirementDialogVisible = true
    },
    async saveRequirement() {
      this.$refs.requirementForm.validate(async valid => {
        if (!valid) return
        try {
          const formData = { ...this.requirementForm }
          Object.keys(formData).forEach(key => {
            if (formData[key] === null || formData[key] === '') {
              if (key === 'position' || ['salary_min', 'salary_max', 'deadline'].includes(key)) formData[key] = null
              else formData[key] = formData[key] || ''
            }
          })
          if (this.requirementForm.id) {
            await this.$http.put(`api/recruitment-requirements/${this.requirementForm.id}/`, formData)
            this.$message.success('更新成功')
          } else {
            await this.$http.post('api/recruitment-requirements/', formData)
            this.$message.success('创建成功')
          }
          this.requirementDialogVisible = false
          this.getRequirementList()
        } catch (error) {
          console.error('保存失败:', error)
          let errorMsg = '保存失败'
          if (error.response && error.response.data) {
            if (error.response.data.detail) {
              const detail = error.response.data.detail
              if (typeof detail === 'object') {
                const errors = []
                Object.keys(detail).forEach(key => { errors.push(Array.isArray(detail[key]) ? `${key}: ${detail[key].join(', ')}` : `${key}: ${detail[key]}`) })
                errorMsg = errors.join('; ')
              } else errorMsg = detail
            } else if (error.response.data.error) errorMsg = error.response.data.error
          }
          this.$message.error(errorMsg)
        }
      })
    },
    async publishRequirement(row) {
      try { await this.$http.post(`api/recruitment-requirements/${row.id}/publish/`); this.$message.success('发布成功'); this.getRequirementList() }
      catch (error) { console.error('发布失败:', error); this.$message.error(error.response && error.response.data.error ? error.response.data.error : '发布失败') }
    },
    async closeRequirement(row) {
      try { await this.$http.post(`api/recruitment-requirements/${row.id}/close/`); this.$message.success('关闭成功'); this.getRequirementList() }
      catch (error) { console.error('关闭失败:', error); this.$message.error(error.response && error.response.data.error ? error.response.data.error : '关闭失败') }
    },
    deleteRequirement(row) {
      this.$confirm('此操作将永久删除该招聘需求，是否继续？', '提示', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
        .then(async () => {
          try { await this.$http.delete(`api/recruitment-requirements/${row.id}/`); this.$message.success('删除成功'); this.getRequirementList() }
          catch (error) { console.error('删除失败:', error); this.$message.error('删除失败') }
        })
        .catch(() => {})
    },
    requirementDialogClosed() { this.$refs.requirementForm && this.$refs.requirementForm.resetFields() },

    async getResumeList() {
      try {
        const params = {}
        if (this.selectedRequirementId) params.recruitment_id = this.selectedRequirementId
        if (this.resumeStatusFilter) params.status = this.resumeStatusFilter
        const { data: res } = await this.$http.get('api/resumes/', { params })
        let list = Array.isArray(res) ? res : []
        if (this.resumeSearch) list = list.filter(item => (item.name && item.name.includes(this.resumeSearch)) || (item.phone && item.phone.includes(this.resumeSearch)))
        this.resumeList = list
        this.resumeTotal = list.length
        this.updateResumeListShow()
      } catch (error) {
        console.error('获取简历列表失败:', error)
        this.$message.error('获取简历列表失败')
        this.resumeList = []
        this.resumeListShow = []
        this.resumeTotal = 0
      }
    },
    showAddResumeDialog() { this.resumeDialogTitle = '添加简历'; this.resumeForm = { id: null, recruitment: '', name: '', phone: '', email: '', gender: '', education: '', work_experience: '', skills: '', source: '', status: 'NEW', note: '' }; this.resumeDialogVisible = true },
    showEditResumeDialog(row) {
      this.resumeDialogTitle = '编辑简历'
      this.resumeForm = { id: row.id, recruitment: row.recruitment_id, name: row.name, phone: row.phone, email: row.email || '', gender: row.gender || '', education: row.education || '', work_experience: row.work_experience || '', skills: row.skills || '', source: row.source || '', status: row.status, note: row.note || '' }
      this.resumeDialogVisible = true
    },
    async saveResume() {
      this.$refs.resumeForm.validate(async valid => {
        if (!valid) return
        try {
          const formData = { ...this.resumeForm }
          Object.keys(formData).forEach(key => { if (formData[key] === '' && key !== 'status') formData[key] = null })
          if (this.resumeForm.id) { await this.$http.put(`api/resumes/${this.resumeForm.id}/`, formData); this.$message.success('更新成功') }
          else { await this.$http.post('api/resumes/', formData); this.$message.success('创建成功') }
          this.resumeDialogVisible = false
          this.getResumeList()
        } catch (error) {
          console.error('保存失败:', error)
          this.$message.error('保存失败')
        }
      })
    },
    showResumeDetail(row) {
      this.$alert(
        `
        <div style="text-align: left; line-height: 1.8;">
          <p><strong>姓名：</strong>${row.name}</p>
          <p><strong>手机号：</strong>${row.phone}</p>
          <p><strong>邮箱：</strong>${row.email || '-'}</p>
          <p><strong>性别：</strong>${row.gender || '-'}</p>
          <p><strong>学历：</strong>${row.education || '-'}</p>
          <p><strong>应聘职位：</strong>${row.recruitment_title || '-'}</p>
          <p><strong>工作经历：</strong>${row.work_experience || '-'}</p>
          <p><strong>技能特长：</strong>${row.skills || '-'}</p>
          <p><strong>简历来源：</strong>${row.source || '-'}</p>
          <p><strong>状态：</strong>${this.getResumeStatusText(row.status)}</p>
          <p><strong>备注：</strong>${row.note || '-'}</p>
        </div>
        `,
        '简历详情',
        { dangerouslyUseHTMLString: true, confirmButtonText: '关闭' }
      )
    },
    deleteResume(row) {
      this.$confirm('此操作将永久删除该简历，是否继续？', '提示', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
        .then(async () => {
          try { await this.$http.delete(`api/resumes/${row.id}/`); this.$message.success('删除成功'); this.getResumeList() }
          catch (error) { console.error('删除失败:', error); this.$message.error('删除失败') }
        })
        .catch(() => {})
    },
    resumeDialogClosed() { this.$refs.resumeForm && this.$refs.resumeForm.resetFields() },

    async getInterviewList() {
      try {
        const params = {}
        if (this.interviewStatusFilter) params.status = this.interviewStatusFilter
        const { data: res } = await this.$http.get('api/interviews/', { params })
        let list = Array.isArray(res) ? res : []
        if (this.interviewSearch) list = list.filter(item => (item.resume_name && item.resume_name.includes(this.interviewSearch)) || (item.resume_phone && item.resume_phone.includes(this.interviewSearch)))
        this.interviewList = list
        this.interviewTotal = list.length
        this.updateInterviewListShow()
      } catch (error) {
        console.error('获取面试列表失败:', error)
        this.$message.error('获取面试列表失败')
        this.interviewList = []
        this.interviewListShow = []
        this.interviewTotal = 0
      }
    },
    showAddInterviewDialog(resume) { this.interviewDialogTitle = '安排面试'; this.interviewForm = { id: null, resume: resume ? resume.id : '', round: 1, interview_type: '', scheduled_time: '', location: '', interviewer_ids: [], status: 'SCHEDULED' }; this.interviewDialogVisible = true },
    showEditInterviewDialog(row) {
      this.interviewDialogTitle = '编辑面试'
      this.interviewForm = { id: row.id, resume: row.resume_id, round: row.round, interview_type: row.interview_type || '', scheduled_time: row.scheduled_time, location: row.location || '', interviewer_ids: row.interviewers_info ? row.interviewers_info.map(i => i.user_id) : [], status: row.status }
      this.interviewDialogVisible = true
    },
    async saveInterview() {
      this.$refs.interviewForm.validate(async valid => {
        if (!valid) return
        try {
          const formData = { ...this.interviewForm }
          Object.keys(formData).forEach(key => { if (formData[key] === '' && key !== 'status' && key !== 'round') formData[key] = null })
          if (this.interviewForm.id) { await this.$http.put(`api/interviews/${this.interviewForm.id}/`, formData); this.$message.success('更新成功') }
          else { await this.$http.post('api/interviews/', formData); this.$message.success('创建成功') }
          this.interviewDialogVisible = false
          this.getInterviewList()
          if (this.activeTab === 'resumes') this.getResumeList()
        } catch (error) {
          console.error('保存失败:', error)
          this.$message.error('保存失败')
        }
      })
    },
    interviewDialogClosed() { this.$refs.interviewForm && this.$refs.interviewForm.resetFields() },

    updateRequirementListShow() { const start = (this.requirementCurrentPage - 1) * this.requirementPageSize; const end = start + this.requirementPageSize; this.requirementListShow = this.requirementList.slice(start, end) },
    handleRequirementSizeChange(pageSize) { this.requirementPageSize = pageSize; this.requirementCurrentPage = 1; this.updateRequirementListShow() },
    handleRequirementCurrentChange(currentPage) { this.requirementCurrentPage = currentPage; this.updateRequirementListShow() },
    updateResumeListShow() { const start = (this.resumeCurrentPage - 1) * this.resumePageSize; const end = start + this.resumePageSize; this.resumeListShow = this.resumeList.slice(start, end) },
    handleResumeSizeChange(pageSize) { this.resumePageSize = pageSize; this.resumeCurrentPage = 1; this.updateResumeListShow() },
    handleResumeCurrentChange(currentPage) { this.resumeCurrentPage = currentPage; this.updateResumeListShow() },
    updateInterviewListShow() { const start = (this.interviewCurrentPage - 1) * this.interviewPageSize; const end = start + this.interviewPageSize; this.interviewListShow = this.interviewList.slice(start, end) },
    handleInterviewSizeChange(pageSize) { this.interviewPageSize = pageSize; this.interviewCurrentPage = 1; this.updateInterviewListShow() },
    handleInterviewCurrentChange(currentPage) { this.interviewCurrentPage = currentPage; this.updateInterviewListShow() },

    showCompleteInterviewDialog(row) { this.completeInterviewForm = { id: row.id, result: row.result || '', score: row.score || null, comment: row.comment || '' }; this.completeInterviewDialogVisible = true },
    async completeInterview() {
      this.$refs.completeInterviewForm.validate(async valid => {
        if (!valid) return
        try {
          await this.$http.post(`api/interviews/${this.completeInterviewForm.id}/complete/`, { result: this.completeInterviewForm.result, score: this.completeInterviewForm.score, comment: this.completeInterviewForm.comment })
          this.$message.success('面试已完成')
          this.completeInterviewDialogVisible = false
          this.getInterviewList()
          if (this.activeTab === 'resumes') this.getResumeList()
        } catch (error) {
          console.error('完成面试失败:', error)
          this.$message.error(error.response && error.response.data.error ? error.response.data.error : '完成面试失败')
        }
      })
    },
    completeInterviewDialogClosed() { this.$refs.completeInterviewForm && this.$refs.completeInterviewForm.resetFields() },
    deleteInterview(row) {
      this.$confirm('此操作将永久删除该面试记录，是否继续？', '提示', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
        .then(async () => {
          try { await this.$http.delete(`api/interviews/${row.id}/`); this.$message.success('删除成功'); this.getInterviewList() }
          catch (error) { console.error('删除失败:', error); this.$message.error('删除失败') }
        })
        .catch(() => {})
    },
  },
}
</script>

<style lang="less" scoped>
.recruitment-page {
  padding: 20px;
  background: linear-gradient(180deg, #f5f8fc 0%, #edf2f9 100%);
  min-height: calc(100vh - 60px);
  .hero-card { margin-top: 16px; margin-bottom: 18px; border: none; border-radius: 14px; background: radial-gradient(circle at 92% 20%, #d8ecff 0%, rgba(216, 236, 255, 0) 40%), #fff; }
  .hero-main { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; h2 { margin: 0; font-size: 24px; color: #0f2d52; } p { margin: 8px 0 0; color: #55708f; font-size: 14px; } }
  .hero-tags { display: flex; gap: 8px; padding-top: 4px; }
  .summary-grid { margin-top: 16px; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
  .summary-item { background: #f7faff; border: 1px solid #dbe9fb; border-radius: 12px; padding: 12px 14px; display: flex; flex-direction: column; gap: 6px; span { font-size: 12px; color: #5d7695; } strong { font-size: 22px; color: #12365f; line-height: 1; } }
  .recruitment-tabs { border-radius: 14px; overflow: hidden; }
  .tab-content { padding: 6px 0 10px; }
  .toolbar-row { margin-bottom: 14px; }
  .toolbar-actions { text-align: right; }
  .data-table { border-radius: 10px; overflow: hidden; }
  .pagination { margin-top: 16px; text-align: right; }
  ::v-deep .el-tabs--border-card { border: none; box-shadow: 0 8px 24px rgba(16, 43, 77, 0.08); }
  ::v-deep .el-tabs__header { background: linear-gradient(90deg, #1b4067 0%, #2e5b8f 100%); margin: 0; border: none; }
  ::v-deep .el-tabs__item { color: rgba(255, 255, 255, 0.72); border: none; }
  ::v-deep .el-tabs__item.is-active { color: #fff; background: rgba(255, 255, 255, 0.08); }
  ::v-deep .el-tabs__content { background: #fff; padding: 18px; }
  ::v-deep .el-table th { background: #f4f8fd; color: #284a71; }
  ::v-deep .el-dialog { border-radius: 12px; }
}
@media (max-width: 992px) { .recruitment-page { .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .toolbar-actions { margin-top: 10px; text-align: left; } } }
@media (max-width: 640px) { .recruitment-page { padding: 12px; .hero-main { flex-direction: column; } .summary-grid { grid-template-columns: 1fr; } } }
</style>
