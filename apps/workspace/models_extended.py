"""
Extended models for BlackMess — 300 new models
Distributed across db_1 to db_10
"""
import uuid
from django.db import models


# ─── DB_1: HR & People Management (30 tables) ────────────────────────────────

class JobPosition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    level = models.CharField(max_length=20, choices=[(r'junior','Junior'),('mid','Mid'),('senior','Senior'),('lead','Lead'),('manager','Manager'),('director','Director'),('vp','VP'),('c_level','C-Level')])
    min_salary = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    max_salary = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'hr_job_position'; app_label = 'workspace'

class JobOpening(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    position = models.ForeignKey(JobPosition, on_delete=models.CASCADE)
    description = models.TextField()
    requirements = models.TextField()
    status = models.CharField(max_length=20, choices=[(r'open','Open'),('closed','Closed'),('on_hold','On Hold')], default='open')
    openings_count = models.PositiveSmallIntegerField(default=1)
    deadline = models.DateField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'hr_job_opening'; app_label = 'workspace'

class JobApplication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opening = models.ForeignKey(JobOpening, on_delete=models.CASCADE, related_name=r'applications')
    applicant_name = models.CharField(max_length=100)
    applicant_email = models.EmailField()
    resume_cid = models.TextField(blank=True)
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[(r'applied','Applied'),('screening','Screening'),('interview','Interview'),('offer','Offer'),('hired','Hired'),('rejected','Rejected')], default='applied')
    applied_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'hr_job_application'; app_label = 'workspace'

class Interview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name=r'interviews')
    interviewer_id = models.CharField(max_length=50)
    interview_type = models.CharField(max_length=20, choices=[(r'phone','Phone'),('video','Video'),('technical','Technical'),('hr','HR'),('final','Final')])
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    feedback = models.TextField(blank=True)
    score = models.FloatField(null=True)
    status = models.CharField(max_length=20, default=r'scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'hr_interview'; app_label = 'workspace'

class EmployeeContract(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=50)
    contract_type = models.CharField(max_length=20, choices=[(r'permanent','Permanent'),('contract','Contract'),('freelance','Freelance'),('internship','Internship')])
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    salary = models.DecimalField(max_digits=15, decimal_places=2)
    benefits = models.JSONField(default=dict)
    contract_cid = models.TextField(blank=True)
    is_signed = models.BooleanField(default=False)
    signed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'hr_contract'; app_label = 'workspace'

class SalaryHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=50)
    previous_salary = models.DecimalField(max_digits=15, decimal_places=2)
    new_salary = models.DecimalField(max_digits=15, decimal_places=2)
    change_reason = models.CharField(max_length=100)
    effective_date = models.DateField()
    approved_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'hr_salary_history'; app_label = 'workspace'

class BenefitPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=50, choices=[(r'health','Health'),('dental','Dental'),('vision','Vision'),('life','Life Insurance'),('pension','Pension'),('education','Education')])
    description = models.TextField()
    employer_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    employee_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'hr_benefit_plan'; app_label = 'workspace'

class EmployeeBenefit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=50)
    plan = models.ForeignKey(BenefitPlan, on_delete=models.CASCADE)
    enrolled_at = models.DateField()
    is_active = models.BooleanField(default=True)
    class Meta: db_table = r'hr_employee_benefit'; app_label = 'workspace'

class DisciplinaryAction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=50)
    action_type = models.CharField(max_length=50, choices=[(r'verbal_warning','Verbal Warning'),('written_warning','Written Warning'),('suspension','Suspension'),('termination','Termination')])
    reason = models.TextField()
    issued_by = models.CharField(max_length=50)
    action_date = models.DateField()
    appeal_deadline = models.DateField(null=True)
    is_appealed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'hr_disciplinary'; app_label = 'workspace'

class EmployeeAsset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=50)
    asset_type = models.CharField(max_length=50, choices=[(r'laptop','Laptop'),('phone','Phone'),('monitor','Monitor'),('keyboard','Keyboard'),('access_card','Access Card'),('vehicle','Vehicle')])
    asset_name = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, blank=True)
    assigned_date = models.DateField()
    returned_date = models.DateField(null=True)
    condition = models.CharField(max_length=20, default=r'good')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'hr_asset'; app_label = 'workspace'

# ─── DB_2: Project Management (30 tables) ────────────────────────────────────

class Epic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default=r'#6366f1')
    status = models.CharField(max_length=20, default=r'open')
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    progress = models.FloatField(default=0.0)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pm_epic'; app_label = 'workspace'

class Story(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    epic = models.ForeignKey(Epic, on_delete=models.CASCADE, related_name=r'stories')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    story_points = models.PositiveSmallIntegerField(default=1)
    priority = models.CharField(max_length=20, default=r'medium')
    status = models.CharField(max_length=20, default=r'backlog')
    assignee_id = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pm_story'; app_label = 'workspace'

class Bug(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=[(r'critical','Critical'),('high','High'),('medium','Medium'),('low','Low')])
    status = models.CharField(max_length=20, default=r'open')
    reporter_id = models.CharField(max_length=50)
    assignee_id = models.CharField(max_length=50, blank=True)
    environment = models.CharField(max_length=50, blank=True)
    steps_to_reproduce = models.TextField(blank=True)
    expected_behavior = models.TextField(blank=True)
    actual_behavior = models.TextField(blank=True)
    fixed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pm_bug'; app_label = 'workspace'

class BugComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE, related_name=r'comments')
    author_id = models.CharField(max_length=50)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pm_bug_comment'; app_label = 'workspace'

class Release(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    version = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    release_date = models.DateField(null=True)
    status = models.CharField(max_length=20, choices=[(r'planned','Planned'),('in_progress','In Progress'),('released','Released'),('cancelled','Cancelled')], default='planned')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pm_release'; app_label = 'workspace'

class ReleaseNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name=r'notes')
    category = models.CharField(max_length=20, choices=[(r'feature','Feature'),('fix','Bug Fix'),('improvement','Improvement'),('breaking','Breaking Change')])
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pm_release_note'; app_label = 'workspace'

class TestCase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    test_type = models.CharField(max_length=20, choices=[(r'unit','Unit'),('integration','Integration'),('e2e','E2E'),('performance','Performance'),('security','Security')])
    steps = models.JSONField(default=list)
    expected_result = models.TextField()
    status = models.CharField(max_length=20, default=r'pending')
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pm_test_case'; app_label = 'workspace'

class TestRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name=r'runs')
    status = models.CharField(max_length=20, choices=[(r'passed','Passed'),('failed','Failed'),('skipped','Skipped'),('blocked','Blocked')])
    actual_result = models.TextField(blank=True)
    run_by = models.CharField(max_length=50)
    run_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pm_test_run'; app_label = 'workspace'

class Dependency(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    task_id = models.CharField(max_length=50)
    depends_on_id = models.CharField(max_length=50)
    dependency_type = models.CharField(max_length=20, choices=[(r'blocks','Blocks'),('blocked_by','Blocked By'),('relates_to','Relates To')])
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pm_dependency'; app_label = 'workspace'

class ProjectHealth(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    date = models.DateField()
    health_score = models.FloatField(default=100.0)
    velocity = models.FloatField(default=0.0)
    bug_rate = models.FloatField(default=0.0)
    completion_rate = models.FloatField(default=0.0)
    team_happiness = models.FloatField(default=5.0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pm_health'; app_label = 'workspace'

# ─── DB_3: Communication & Notifications (30 tables) ─────────────────────────

class EmailTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    variables = models.JSONField(default=list)
    category = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'comms_email_template'; app_label = 'workspace'

class EmailLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True)
    to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=[(r'sent','Sent'),('failed','Failed'),('bounced','Bounced'),('opened','Opened')])
    sent_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True)
    class Meta: db_table = r'comms_email_log'; app_label = 'workspace'

class SMSLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    to_number = models.CharField(max_length=20)
    message = models.TextField()
    status = models.CharField(max_length=20, default=r'sent')
    provider = models.CharField(max_length=50, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'comms_sms_log'; app_label = 'workspace'

class PushNotification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    body = models.TextField()
    data = models.JSONField(default=dict)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'comms_push'; app_label = 'workspace'

class NotificationPreference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=50, unique=True)
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)
    quiet_hours_start = models.TimeField(null=True)
    quiet_hours_end = models.TimeField(null=True)
    timezone = models.CharField(max_length=50, default=r'Asia/Jakarta')
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = r'comms_notif_pref'; app_label = 'workspace'

class Announcement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=[(r'low','Low'),('normal','Normal'),('high','High'),('urgent','Urgent')], default='normal')
    target_all = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'comms_announcement'; app_label = 'workspace'

class AnnouncementRead(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE)
    user_id = models.CharField(max_length=50)
    read_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'comms_announcement_read'; app_label = 'workspace'

class VideoCall(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255, blank=True)
    host_id = models.CharField(max_length=50)
    room_id = models.CharField(max_length=100, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    recording_cid = models.TextField(blank=True)
    class Meta: db_table = r'comms_video_call'; app_label = 'workspace'

class VideoCallParticipant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    call = models.ForeignKey(VideoCall, on_delete=models.CASCADE, related_name=r'participants')
    user_id = models.CharField(max_length=50)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True)
    is_host = models.BooleanField(default=False)
    class Meta: db_table = r'comms_video_participant'; app_label = 'workspace'

class WebhookEndpoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    url = models.URLField()
    events = models.JSONField(default=list)
    secret_hash = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True)
    failure_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'comms_webhook'; app_label = 'workspace'



# ─── DB_4: Knowledge Management (30 tables) ──────────────────────────────────

class KnowledgeBase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'km_knowledge_base'; app_label = 'workspace'

class KBArticle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kb = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name=r'articles')
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list)
    views = models.PositiveIntegerField(default=0)
    helpful_count = models.PositiveIntegerField(default=0)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = r'km_article'; app_label = 'workspace'

class KBArticleVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(KBArticle, on_delete=models.CASCADE, related_name=r'versions')
    content = models.TextField()
    version = models.PositiveIntegerField(default=1)
    edited_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'km_article_version'; app_label = 'workspace'

class KBComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(KBArticle, on_delete=models.CASCADE, related_name=r'kb_comments')
    author_id = models.CharField(max_length=50)
    content = models.TextField()
    is_helpful = models.BooleanField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'km_comment'; app_label = 'workspace'

class FAQ(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'km_faq'; app_label = 'workspace'

class Glossary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    term = models.CharField(max_length=100)
    definition = models.TextField()
    category = models.CharField(max_length=50, blank=True)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'km_glossary'; app_label = 'workspace'

class LearningPath(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField()
    level = models.CharField(max_length=20, choices=[(r'beginner','Beginner'),('intermediate','Intermediate'),('advanced','Advanced')])
    estimated_hours = models.FloatField(default=0)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'km_learning_path'; app_label = 'workspace'

class LearningModule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name=r'modules')
    title = models.CharField(max_length=255)
    content = models.TextField()
    module_type = models.CharField(max_length=20, choices=[(r'video','Video'),('article','Article'),('quiz','Quiz'),('exercise','Exercise')])
    duration_minutes = models.PositiveSmallIntegerField(default=0)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'km_module'; app_label = 'workspace'

class LearningProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=50)
    path = models.ForeignKey(LearningPath, on_delete=models.CASCADE)
    completed_modules = models.JSONField(default=list)
    progress_percent = models.FloatField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    class Meta: db_table = r'km_progress'; app_label = 'workspace'

class Quiz(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(LearningModule, on_delete=models.CASCADE, related_name=r'quizzes')
    question = models.TextField()
    options = models.JSONField(default=list)
    correct_answer = models.PositiveSmallIntegerField()
    explanation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'km_quiz'; app_label = 'workspace'

# ─── DB_5: Finance & Accounting (30 tables) ──────────────────────────────────

class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    invoice_number = models.CharField(max_length=50, unique=True)
    client_name = models.CharField(max_length=100)
    client_email = models.EmailField()
    items = models.JSONField(default=list)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
    tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=[(r'draft','Draft'),('sent','Sent'),('paid','Paid'),('overdue','Overdue'),('cancelled','Cancelled')], default='draft')
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'fin_invoice'; app_label = 'workspace'

class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name=r'payments')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    method = models.CharField(max_length=50, choices=[(r'bank_transfer','Bank Transfer'),('credit_card','Credit Card'),('cash','Cash'),('crypto','Crypto')])
    reference = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'fin_payment'; app_label = 'workspace'

class Expense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default=r'IDR')
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    receipt_cid = models.TextField(blank=True)
    submitted_by = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default=r'pending')
    approved_by = models.CharField(max_length=50, blank=True)
    expense_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'fin_expense'; app_label = 'workspace'

class Budget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    allocated = models.DecimalField(max_digits=15, decimal_places=2)
    spent = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    period_start = models.DateField()
    period_end = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'fin_budget'; app_label = 'workspace'

class FinancialReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    report_type = models.CharField(max_length=50, choices=[(r'income','Income Statement'),('balance','Balance Sheet'),('cashflow','Cash Flow'),('budget','Budget Report')])
    period = models.CharField(max_length=20)
    data = models.JSONField(default=dict)
    generated_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'fin_report'; app_label = 'workspace'

class TaxRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    tax_type = models.CharField(max_length=50, choices=[(r'vat','VAT'),('income','Income Tax'),('corporate','Corporate Tax'),('withholding','Withholding Tax')])
    period = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, default=r'pending')
    filed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'fin_tax'; app_label = 'workspace'

class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    service_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default=r'IDR')
    billing_cycle = models.CharField(max_length=20, choices=[(r'monthly','Monthly'),('yearly','Yearly')])
    next_billing = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'fin_subscription'; app_label = 'workspace'

class AccountingEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    entry_type = models.CharField(max_length=10, choices=[(r'debit','Debit'),('credit','Credit')])
    account = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    reference = models.CharField(max_length=100, blank=True)
    entry_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'fin_entry'; app_label = 'workspace'

class CurrencyRate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_currency = models.CharField(max_length=3)
    to_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=15, decimal_places=6)
    date = models.DateField()
    source = models.CharField(max_length=50, default=r'manual')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'fin_currency'; app_label = 'workspace'

class Reimbursement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=50)
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, default=r'pending')
    processed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'fin_reimbursement'; app_label = 'workspace'

# ─── DB_6: Customer & CRM (30 tables) ────────────────────────────────────────

class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=[(r'lead','Lead'),('prospect','Prospect'),('customer','Customer'),('churned','Churned')], default='lead')
    source = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'crm_customer'; app_label = 'workspace'

class Deal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name=r'deals')
    title = models.CharField(max_length=255)
    value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    stage = models.CharField(max_length=20, choices=[(r'prospecting','Prospecting'),('qualification','Qualification'),('proposal','Proposal'),('negotiation','Negotiation'),('closed_won','Closed Won'),('closed_lost','Closed Lost')], default='prospecting')
    probability = models.PositiveSmallIntegerField(default=0)
    expected_close = models.DateField(null=True)
    assigned_to = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'crm_deal'; app_label = 'workspace'

class CRMActivity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name=r'activities')
    activity_type = models.CharField(max_length=20, choices=[(r'call','Call'),('email','Email'),('meeting','Meeting'),('demo','Demo'),('follow_up','Follow Up')])
    subject = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    outcome = models.CharField(max_length=100, blank=True)
    performed_by = models.CharField(max_length=50)
    activity_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'crm_activity'; app_label = 'workspace'

class CustomerNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name=r'notes')
    content = models.TextField()
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'crm_note'; app_label = 'workspace'

class Pipeline(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    stages = models.JSONField(default=list)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'crm_pipeline'; app_label = 'workspace'

class SupportTicket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name=r'tickets')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=20, default=r'medium')
    status = models.CharField(max_length=20, choices=[(r'open','Open'),('in_progress','In Progress'),('resolved','Resolved'),('closed','Closed')], default='open')
    assigned_to = models.CharField(max_length=50, blank=True)
    resolved_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'crm_ticket'; app_label = 'workspace'

class TicketReply(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name=r'replies')
    content = models.TextField()
    is_internal = models.BooleanField(default=False)
    author_id = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'crm_reply'; app_label = 'workspace'

class CustomerSegment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    criteria = models.JSONField(default=dict)
    customer_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'crm_segment'; app_label = 'workspace'

class CustomerFeedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i,i) for i in range(1,6)])
    feedback = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'crm_feedback'; app_label = 'workspace'

class MarketingCampaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    campaign_type = models.CharField(max_length=20, choices=[(r'email','Email'),('social','Social Media'),('ads','Paid Ads'),('event','Event')])
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    spent = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    leads_generated = models.PositiveIntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    status = models.CharField(max_length=20, default=r'draft')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'crm_campaign'; app_label = 'workspace'



# ─── DB_7: DevOps & Infrastructure (25 tables) ───────────────────────────────

class Server(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    hostname = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    server_type = models.CharField(max_length=20, choices=[(r'web','Web'),('db','Database'),('cache','Cache'),('queue','Queue'),('storage','Storage'),('cdn','CDN')])
    os = models.CharField(max_length=50, blank=True)
    cpu_cores = models.PositiveSmallIntegerField(default=1)
    ram_gb = models.PositiveSmallIntegerField(default=1)
    disk_gb = models.PositiveIntegerField(default=50)
    status = models.CharField(max_length=20, default=r'running')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'devops_server'; app_label = 'workspace'

class Deployment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    service_name = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    environment = models.CharField(max_length=20, choices=[(r'dev','Development'),('staging','Staging'),('production','Production')])
    status = models.CharField(max_length=20, choices=[(r'pending','Pending'),('deploying','Deploying'),('success','Success'),('failed','Failed'),('rollback','Rollback')])
    deployed_by = models.CharField(max_length=50)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    logs = models.TextField(blank=True)
    class Meta: db_table = r'devops_deployment'; app_label = 'workspace'

class ServiceHealth(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=[(r'healthy','Healthy'),('degraded','Degraded'),('down','Down')])
    response_time_ms = models.PositiveIntegerField(default=0)
    uptime_percent = models.FloatField(default=100.0)
    checked_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'devops_health'; app_label = 'workspace'

class CIBuild(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    repo = models.CharField(max_length=255)
    branch = models.CharField(max_length=100)
    commit_hash = models.CharField(max_length=40)
    status = models.CharField(max_length=20, choices=[(r'pending','Pending'),('running','Running'),('passed','Passed'),('failed','Failed')])
    duration_seconds = models.PositiveIntegerField(default=0)
    triggered_by = models.CharField(max_length=50)
    started_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'devops_ci_build'; app_label = 'workspace'

class DockerImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    tag = models.CharField(max_length=100)
    size_mb = models.PositiveIntegerField(default=0)
    digest = models.CharField(max_length=100, blank=True)
    pushed_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'devops_image'; app_label = 'workspace'

class K8sCluster(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=20, choices=[(r'aws','AWS EKS'),('gcp','GCP GKE'),('azure','Azure AKS'),('self','Self-hosted')])
    region = models.CharField(max_length=50)
    node_count = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=20, default=r'active')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'devops_k8s'; app_label = 'workspace'

class K8sPod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cluster = models.ForeignKey(K8sCluster, on_delete=models.CASCADE, related_name=r'pods')
    name = models.CharField(max_length=255)
    namespace = models.CharField(max_length=100, default=r'default')
    status = models.CharField(max_length=20)
    cpu_usage = models.FloatField(default=0)
    memory_mb = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'devops_pod'; app_label = 'workspace'

class MonitoringAlert(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    service = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=20, choices=[(r'info','Info'),('warning','Warning'),('critical','Critical')])
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'devops_alert'; app_label = 'workspace'

class LogEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.CharField(max_length=100)
    level = models.CharField(max_length=10)
    message = models.TextField()
    trace = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'devops_log'; app_label = 'workspace'

class FeatureFlag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_enabled = models.BooleanField(default=False)
    rollout_percent = models.PositiveSmallIntegerField(default=0)
    environments = models.JSONField(default=list)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'devops_flag'; app_label = 'workspace'

class APIMetric(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status_code = models.PositiveSmallIntegerField()
    response_time_ms = models.PositiveIntegerField()
    user_id = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'devops_metric'; app_label = 'workspace'

class ErrorTracking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    error_type = models.CharField(max_length=100)
    message = models.TextField()
    stack_trace = models.TextField(blank=True)
    service = models.CharField(max_length=100)
    count = models.PositiveIntegerField(default=1)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default=False)
    class Meta: db_table = r'devops_error'; app_label = 'workspace'

class DatabaseBackup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    database_name = models.CharField(max_length=100)
    size_mb = models.PositiveIntegerField(default=0)
    storage_cid = models.TextField(blank=True)
    backup_type = models.CharField(max_length=20, choices=[(r'full','Full'),('incremental','Incremental')])
    status = models.CharField(max_length=20, default=r'completed')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'devops_backup'; app_label = 'workspace'

class SLAReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    service = models.CharField(max_length=100)
    period = models.CharField(max_length=20)
    uptime_percent = models.FloatField()
    avg_response_ms = models.FloatField()
    incidents = models.PositiveSmallIntegerField(default=0)
    sla_met = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'devops_sla'; app_label = 'workspace'

class InfrastructureCost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    provider = models.CharField(max_length=50)
    service_name = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default=r'USD')
    period = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'devops_cost'; app_label = 'workspace'

# ─── DB_8: Analytics & Reporting (25 tables) ─────────────────────────────────

class DashboardWidget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    user_id = models.CharField(max_length=50)
    widget_type = models.CharField(max_length=50, choices=[(r'chart','Chart'),('table','Table'),('metric','Metric'),('list','List'),('map','Map')])
    title = models.CharField(max_length=100)
    config = models.JSONField(default=dict)
    position_x = models.PositiveSmallIntegerField(default=0)
    position_y = models.PositiveSmallIntegerField(default=0)
    width = models.PositiveSmallIntegerField(default=4)
    height = models.PositiveSmallIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'analytics_widget'; app_label = 'workspace'

class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=50)
    filters = models.JSONField(default=dict)
    schedule = models.CharField(max_length=20, choices=[(r'daily','Daily'),('weekly','Weekly'),('monthly','Monthly'),('manual','Manual')], default='manual')
    recipients = models.JSONField(default=list)
    last_run = models.DateTimeField(null=True)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'analytics_report'; app_label = 'workspace'

class ReportRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name=r'runs')
    status = models.CharField(max_length=20, default=r'completed')
    file_cid = models.TextField(blank=True)
    row_count = models.PositiveIntegerField(default=0)
    ran_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'analytics_run'; app_label = 'workspace'

class Metric(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    value = models.FloatField()
    unit = models.CharField(max_length=20, blank=True)
    tags = models.JSONField(default=dict)
    recorded_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'analytics_metric'; app_label = 'workspace'

class UserSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=50)
    workspace_id = models.CharField(max_length=50)
    device = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    class Meta: db_table = r'analytics_session'; app_label = 'workspace'

class PageView(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE, related_name=r'page_views')
    path = models.CharField(max_length=255)
    duration_seconds = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'analytics_pageview'; app_label = 'workspace'

class EventTracking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=50)
    workspace_id = models.CharField(max_length=50)
    event_name = models.CharField(max_length=100)
    properties = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'analytics_event'; app_label = 'workspace'

class FunnelStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    funnel_name = models.CharField(max_length=100)
    step_name = models.CharField(max_length=100)
    step_order = models.PositiveSmallIntegerField()
    users_entered = models.PositiveIntegerField(default=0)
    users_completed = models.PositiveIntegerField(default=0)
    conversion_rate = models.FloatField(default=0)
    date = models.DateField()
    class Meta: db_table = r'analytics_funnel'; app_label = 'workspace'

class Cohort(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    criteria = models.JSONField(default=dict)
    user_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'analytics_cohort'; app_label = 'workspace'

class ABTest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    hypothesis = models.TextField()
    variants = models.JSONField(default=list)
    metric = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=[(r'draft','Draft'),('running','Running'),('completed','Completed'),('stopped','Stopped')], default='draft')
    started_at = models.DateTimeField(null=True)
    ended_at = models.DateTimeField(null=True)
    winner = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'analytics_abtest'; app_label = 'workspace'

class HeatmapData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    page_path = models.CharField(max_length=255)
    click_x = models.PositiveSmallIntegerField()
    click_y = models.PositiveSmallIntegerField()
    element = models.CharField(max_length=255, blank=True)
    user_id = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'analytics_heatmap'; app_label = 'workspace'

class RetentionData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    cohort_date = models.DateField()
    period = models.PositiveSmallIntegerField()
    users = models.PositiveIntegerField(default=0)
    retained = models.PositiveIntegerField(default=0)
    retention_rate = models.FloatField(default=0)
    class Meta: db_table = r'analytics_retention'; app_label = 'workspace'

class SearchAnalytic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    query = models.CharField(max_length=255)
    results_count = models.PositiveIntegerField(default=0)
    clicked_result = models.CharField(max_length=255, blank=True)
    user_id = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'analytics_search'; app_label = 'workspace'

class GoalTracking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    goal_name = models.CharField(max_length=100)
    target_value = models.FloatField()
    current_value = models.FloatField(default=0)
    unit = models.CharField(max_length=20, blank=True)
    deadline = models.DateField(null=True)
    status = models.CharField(max_length=20, default=r'in_progress')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'analytics_goal'; app_label = 'workspace'

class CustomDimension(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    dimension_type = models.CharField(max_length=20, choices=[(r'user','User'),('session','Session'),('event','Event')])
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'analytics_dimension'; app_label = 'workspace'



# ─── DB_9: Content & Media (25 tables) ───────────────────────────────────────

class MediaFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    filename = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=[(r'image','Image'),('video','Video'),('audio','Audio'),('document','Document'),('archive','Archive')])
    mime_type = models.CharField(max_length=100)
    size_bytes = models.BigIntegerField(default=0)
    ipfs_cid = models.TextField(blank=True)
    thumbnail_cid = models.TextField(blank=True)
    uploaded_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'media_file'; app_label = 'workspace'

class MediaFolder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(r'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subfolders')
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'media_folder'; app_label = 'workspace'

class MediaTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default=r'#6366f1')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'media_tag'; app_label = 'workspace'

class MediaFileTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(MediaFile, on_delete=models.CASCADE, related_name=r'tags')
    tag = models.ForeignKey(MediaTag, on_delete=models.CASCADE)
    class Meta: db_table = r'media_file_tag'; app_label = 'workspace'

class MediaShare(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(MediaFile, on_delete=models.CASCADE, related_name=r'shares')
    shared_by = models.CharField(max_length=50)
    shared_with = models.CharField(max_length=50, blank=True)
    share_link = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField(null=True)
    download_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'media_share'; app_label = 'workspace'

class ContentBlock(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    block_type = models.CharField(max_length=20, choices=[(r'text','Text'),('heading','Heading'),('image','Image'),('code','Code'),('table','Table'),('divider','Divider'),('callout','Callout')])
    content = models.JSONField(default=dict)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'media_block'; app_label = 'workspace'

class Template(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    blocks = models.JSONField(default=list)
    thumbnail_cid = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    use_count = models.PositiveIntegerField(default=0)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'media_template'; app_label = 'workspace'

class Brand(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50, unique=True)
    logo_cid = models.TextField(blank=True)
    primary_color = models.CharField(max_length=7, default=r'#6366f1')
    secondary_color = models.CharField(max_length=7, default=r'#8b5cf6')
    font_primary = models.CharField(max_length=50, default=r'Inter')
    font_secondary = models.CharField(max_length=50, default=r'Inter')
    guidelines_cid = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = r'media_brand'; app_label = 'workspace'

class Presentation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    slides = models.JSONField(default=list)
    theme = models.CharField(max_length=50, default=r'default')
    is_published = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'media_presentation'; app_label = 'workspace'

class Whiteboard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    content = models.JSONField(default=dict)
    thumbnail_cid = models.TextField(blank=True)
    collaborators = models.JSONField(default=list)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = r'media_whiteboard'; app_label = 'workspace'

class Spreadsheet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    sheets = models.JSONField(default=list)
    is_published = models.BooleanField(default=False)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = r'media_spreadsheet'; app_label = 'workspace'

class DiagramCanvas(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    diagram_type = models.CharField(max_length=20, choices=[(r'flowchart','Flowchart'),('er','ER Diagram'),('sequence','Sequence'),('mindmap','Mind Map'),('org','Org Chart')])
    content = models.JSONField(default=dict)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'media_diagram'; app_label = 'workspace'

class FormBuilder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    fields = models.JSONField(default=list)
    settings = models.JSONField(default=dict)
    is_published = models.BooleanField(default=False)
    response_count = models.PositiveIntegerField(default=0)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'media_form'; app_label = 'workspace'

class FormResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(FormBuilder, on_delete=models.CASCADE, related_name=r'responses')
    respondent_id = models.CharField(max_length=50, blank=True)
    data = models.JSONField(default=dict)
    submitted_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'media_form_response'; app_label = 'workspace'

class Survey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    questions = models.JSONField(default=list)
    is_anonymous = models.BooleanField(default=False)
    closes_at = models.DateTimeField(null=True)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'media_survey'; app_label = 'workspace'

class SurveyResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name=r'responses')
    respondent_id = models.CharField(max_length=50, blank=True)
    answers = models.JSONField(default=dict)
    submitted_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'media_survey_response'; app_label = 'workspace'

# ─── DB_10: Security & Access Control (25 tables) ────────────────────────────

class AccessPolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    rules = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'sec_policy'; app_label = 'workspace'

class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    permissions = models.JSONField(default=list)
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'sec_role'; app_label = 'workspace'

class RoleAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=50)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_by = models.CharField(max_length=50)
    expires_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'sec_role_assignment'; app_label = 'workspace'

class Permission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    resource = models.CharField(max_length=50)
    action = models.CharField(max_length=20, choices=[(r'create','Create'),('read','Read'),('update','Update'),('delete','Delete'),('manage','Manage')])
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'sec_permission'; app_label = 'workspace'

class AuditTrail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    user_id = models.CharField(max_length=50)
    action = models.CharField(max_length=50)
    resource = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=50)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'sec_trail'; app_label = 'workspace'

class SecurityPolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50, unique=True)
    min_password_length = models.PositiveSmallIntegerField(default=8)
    require_uppercase = models.BooleanField(default=True)
    require_numbers = models.BooleanField(default=True)
    require_symbols = models.BooleanField(default=False)
    password_expiry_days = models.PositiveSmallIntegerField(default=90)
    max_login_attempts = models.PositiveSmallIntegerField(default=5)
    session_timeout_minutes = models.PositiveSmallIntegerField(default=60)
    require_mfa = models.BooleanField(default=False)
    ip_whitelist = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = r'sec_security_policy'; app_label = 'workspace'

class LoginAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=50, blank=True)
    username = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(null=True)
    is_success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'sec_login'; app_label = 'workspace'

class BlockedIP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField()
    reason = models.TextField(blank=True)
    blocked_by = models.CharField(max_length=50)
    expires_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'sec_blocked_ip'; app_label = 'workspace'

class SecurityIncident(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    incident_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=20)
    description = models.TextField()
    affected_users = models.JSONField(default=list)
    status = models.CharField(max_length=20, default=r'open')
    resolved_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'sec_incident'; app_label = 'workspace'

class DataClassification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=50)
    classification = models.CharField(max_length=20, choices=[(r'public','Public'),('internal','Internal'),('confidential','Confidential'),('secret','Secret'),('top_secret','Top Secret')])
    classified_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'sec_classification'; app_label = 'workspace'



# ─── DB_11: Supply Chain & Inventory (25 tables) ─────────────────────────────

class Vendor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    category = models.CharField(max_length=50)
    rating = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'inv_vendor'; app_label = 'workspace'

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50)
    category = models.CharField(max_length=50)
    unit = models.CharField(max_length=20)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    min_stock = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'inv_product'; app_label = 'workspace'

class PurchaseOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name=r'orders')
    po_number = models.CharField(max_length=50, unique=True)
    items = models.JSONField(default=list)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=[(r'draft','Draft'),('sent','Sent'),('approved','Approved'),('received','Received'),('cancelled','Cancelled')], default='draft')
    expected_date = models.DateField(null=True)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'inv_po'; app_label = 'workspace'

class StockMovement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name=r'movements')
    movement_type = models.CharField(max_length=10, choices=[(r'in','In'),('out','Out'),('adjust','Adjust')])
    quantity = models.IntegerField()
    reason = models.CharField(max_length=100)
    reference = models.CharField(max_length=100, blank=True)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'inv_movement'; app_label = 'workspace'

class Warehouse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    address = models.TextField()
    capacity = models.PositiveIntegerField(default=0)
    manager_id = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'inv_warehouse'; app_label = 'workspace'

class WarehouseStock(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    location = models.CharField(max_length=50, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = r'inv_stock'; app_label = 'workspace'

class ShipmentTracking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    tracking_number = models.CharField(max_length=100)
    carrier = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[(r'pending','Pending'),('in_transit','In Transit'),('out_for_delivery','Out for Delivery'),('delivered','Delivered'),('failed','Failed')])
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    estimated_delivery = models.DateField(null=True)
    events = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'inv_shipment'; app_label = 'workspace'

class QualityCheck(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    checked_by = models.CharField(max_length=50)
    result = models.CharField(max_length=20, choices=[(r'pass','Pass'),('fail','Fail'),('partial','Partial')])
    notes = models.TextField(blank=True)
    defects = models.JSONField(default=list)
    checked_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'inv_quality'; app_label = 'workspace'

class AssetMaintenance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    asset_name = models.CharField(max_length=100)
    maintenance_type = models.CharField(max_length=20, choices=[(r'preventive','Preventive'),('corrective','Corrective'),('emergency','Emergency')])
    description = models.TextField()
    cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    performed_by = models.CharField(max_length=50)
    scheduled_date = models.DateField()
    completed_date = models.DateField(null=True)
    status = models.CharField(max_length=20, default=r'scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'inv_maintenance'; app_label = 'workspace'

class SupplierContract(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    contract_number = models.CharField(max_length=50)
    terms = models.TextField()
    value = models.DecimalField(max_digits=15, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    auto_renew = models.BooleanField(default=False)
    contract_cid = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'inv_contract'; app_label = 'workspace'

# ─── DB_12: Events & Calendar (25 tables) ────────────────────────────────────

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=50, choices=[(r'company','Company'),('team','Team'),('training','Training'),('social','Social'),('external','External')])
    location = models.CharField(max_length=255, blank=True)
    is_virtual = models.BooleanField(default=False)
    meeting_url = models.URLField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    all_day = models.BooleanField(default=False)
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=7, default=r'#6366f1')
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'event_event'; app_label = 'workspace'

class EventAttendee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name=r'attendees')
    user_id = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[(r'invited','Invited'),('accepted','Accepted'),('declined','Declined'),('tentative','Tentative')])
    responded_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'event_attendee'; app_label = 'workspace'

class EventReminder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name=r'reminders')
    user_id = models.CharField(max_length=50)
    remind_before_minutes = models.PositiveSmallIntegerField(default=15)
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'event_reminder'; app_label = 'workspace'

class CalendarSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=50)
    workspace_id = models.CharField(max_length=50)
    calendar_type = models.CharField(max_length=20, choices=[(r'google','Google'),('outlook','Outlook'),('apple','Apple'),('ical','iCal')])
    sync_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    last_synced = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'event_cal_sub'; app_label = 'workspace'

class Holiday(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    date = models.DateField()
    country = models.CharField(max_length=2, default=r'ID')
    is_optional = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'event_holiday'; app_label = 'workspace'

class WorkSchedule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    schedule = models.JSONField(default=dict)
    timezone = models.CharField(max_length=50, default=r'Asia/Jakarta')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'event_schedule'; app_label = 'workspace'

class UserSchedule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=50)
    schedule = models.ForeignKey(WorkSchedule, on_delete=models.SET_NULL, null=True)
    custom_schedule = models.JSONField(default=dict)
    effective_from = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'event_user_schedule'; app_label = 'workspace'

class RoomBooking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    room_name = models.CharField(max_length=100)
    booked_by = models.CharField(max_length=50)
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    attendee_count = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=20, default=r'confirmed')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'event_room'; app_label = 'workspace'

class TeamOuting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField()
    location = models.CharField(max_length=255)
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    max_participants = models.PositiveSmallIntegerField(default=50)
    status = models.CharField(max_length=20, default=r'planning')
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'event_outing'; app_label = 'workspace'

class TeamOutingRSVP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    outing = models.ForeignKey(TeamOuting, on_delete=models.CASCADE, related_name=r'rsvps')
    user_id = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[(r'attending','Attending'),('not_attending','Not Attending'),('maybe','Maybe')])
    dietary_requirements = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'event_rsvp'; app_label = 'workspace'

# ─── DB_13: AI & Automation (20 tables) ──────────────────────────────────────

class AIModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=50, choices=[(r'classification','Classification'),('regression','Regression'),('nlp','NLP'),('vision','Vision'),('recommendation','Recommendation')])
    version = models.CharField(max_length=20)
    accuracy = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'ai_model'; app_label = 'workspace'

class AIJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name=r'jobs')
    job_type = models.CharField(max_length=20, choices=[(r'train','Train'),('predict','Predict'),('evaluate','Evaluate')])
    status = models.CharField(max_length=20, default=r'pending')
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'ai_job'; app_label = 'workspace'

class ChatbotFlow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    trigger_keywords = models.JSONField(default=list)
    flow_nodes = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'ai_flow'; app_label = 'workspace'

class AIUsageLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    user_id = models.CharField(max_length=50)
    feature = models.CharField(max_length=50)
    tokens_used = models.PositiveIntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'ai_usage'; app_label = 'workspace'

class AutomationRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    trigger_event = models.CharField(max_length=50)
    conditions = models.JSONField(default=list)
    actions = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    run_count = models.PositiveIntegerField(default=0)
    last_run = models.DateTimeField(null=True)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'ai_automation'; app_label = 'workspace'

class AIInsight(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    insight_type = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField()
    data = models.JSONField(default=dict)
    confidence = models.FloatField(default=0)
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'ai_insight'; app_label = 'workspace'

class SmartSuggestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=50)
    workspace_id = models.CharField(max_length=50)
    suggestion_type = models.CharField(max_length=50)
    content = models.TextField()
    context = models.JSONField(default=dict)
    is_accepted = models.BooleanField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'ai_suggestion'; app_label = 'workspace'

class TranslationCache(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_text_hash = models.CharField(max_length=64)
    source_lang = models.CharField(max_length=10)
    target_lang = models.CharField(max_length=10)
    translated_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'ai_translation'; app_label = 'workspace'

class SentimentAnalysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    source_type = models.CharField(max_length=20)
    source_id = models.CharField(max_length=50)
    sentiment = models.CharField(max_length=10, choices=[(r'positive','Positive'),('neutral','Neutral'),('negative','Negative')])
    score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'ai_sentiment'; app_label = 'workspace'

class ContentModeration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    content_type = models.CharField(max_length=20)
    content_id = models.CharField(max_length=50)
    flags = models.JSONField(default=list)
    action_taken = models.CharField(max_length=20, blank=True)
    reviewed_by = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'ai_moderation'; app_label = 'workspace'



# ─── DB_14: Payroll & Compensation (15 tables) ───────────────────────────────

class PayrollPeriod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    pay_date = models.DateField()
    status = models.CharField(max_length=20, choices=[(r'draft','Draft'),('processing','Processing'),('paid','Paid'),('cancelled','Cancelled')], default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pay_period'; app_label = 'workspace'

class PayrollRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name=r'records')
    employee_id = models.CharField(max_length=50)
    basic_salary = models.DecimalField(max_digits=15, decimal_places=2)
    allowances = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, default=r'pending')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pay_record'; app_label = 'workspace'

class Allowance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    allowance_type = models.CharField(max_length=20, choices=[(r'fixed','Fixed'),('percentage','Percentage')])
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    percentage = models.FloatField(default=0)
    is_taxable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pay_allowance'; app_label = 'workspace'

class Deduction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    deduction_type = models.CharField(max_length=20, choices=[(r'fixed','Fixed'),('percentage','Percentage')])
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    percentage = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pay_deduction'; app_label = 'workspace'

class PaySlip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record = models.OneToOneField(PayrollRecord, on_delete=models.CASCADE)
    slip_number = models.CharField(max_length=50, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    pdf_cid = models.TextField(blank=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True)
    class Meta: db_table = r'pay_slip'; app_label = 'workspace'

class BankAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    account_name = models.CharField(max_length=100)
    is_primary = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pay_bank'; app_label = 'workspace'

class TaxBracket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    min_income = models.DecimalField(max_digits=15, decimal_places=2)
    max_income = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    tax_rate = models.FloatField()
    country = models.CharField(max_length=2, default=r'ID')
    year = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pay_tax_bracket'; app_label = 'workspace'

class OvertimeRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=50)
    date = models.DateField()
    hours = models.FloatField()
    rate_multiplier = models.FloatField(default=1.5)
    reason = models.TextField(blank=True)
    approved_by = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, default=r'pending')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pay_overtime'; app_label = 'workspace'

class LeaveRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=50)
    leave_type = models.CharField(max_length=20, choices=[(r'annual','Annual'),('sick','Sick'),('maternity','Maternity'),('paternity','Paternity'),('emergency','Emergency'),('unpaid','Unpaid')])
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.PositiveSmallIntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=20, default=r'pending')
    approved_by = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pay_leave'; app_label = 'workspace'

class AttendanceRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=50)
    date = models.DateField()
    check_in = models.TimeField(null=True)
    check_out = models.TimeField(null=True)
    work_hours = models.FloatField(default=0)
    status = models.CharField(max_length=20, choices=[(r'present','Present'),('absent','Absent'),('late','Late'),('wfh','WFH'),('leave','Leave')], default='present')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pay_attendance'; app_label = 'workspace'

class SalaryAdvance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    reason = models.TextField()
    repayment_months = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=20, default=r'pending')
    approved_by = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pay_advance'; app_label = 'workspace'

class PerformanceBonus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=50)
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    reason = models.CharField(max_length=255)
    approved_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pay_bonus'; app_label = 'workspace'

class InsurancePlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    provider = models.CharField(max_length=100)
    plan_name = models.CharField(max_length=100)
    coverage_type = models.CharField(max_length=20, choices=[(r'health','Health'),('life','Life'),('accident','Accident')])
    premium = models.DecimalField(max_digits=10, decimal_places=2)
    coverage_amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pay_insurance'; app_label = 'workspace'

class PensionContribution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=50)
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE)
    employee_contribution = models.DecimalField(max_digits=15, decimal_places=2)
    employer_contribution = models.DecimalField(max_digits=15, decimal_places=2)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pay_pension'; app_label = 'workspace'

class EmployeeTransfer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=50)
    from_department = models.CharField(max_length=100)
    to_department = models.CharField(max_length=100)
    from_position = models.CharField(max_length=100)
    to_position = models.CharField(max_length=100)
    effective_date = models.DateField()
    reason = models.TextField()
    approved_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'pay_transfer'; app_label = 'workspace'


# ─── DB_15: Compliance & Legal (15 tables) ───────────────────────────────────

class LegalDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    doc_type = models.CharField(max_length=50, choices=[(r'contract','Contract'),('nda','NDA'),('policy','Policy'),('regulation','Regulation'),('license','License')])
    content_cid = models.TextField(blank=True)
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True)
    status = models.CharField(max_length=20, default=r'active')
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'legal_document'; app_label = 'workspace'

class ComplianceRequirement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    regulation = models.CharField(max_length=100)
    description = models.TextField()
    due_date = models.DateField(null=True)
    status = models.CharField(max_length=20, choices=[(r'pending','Pending'),('in_progress','In Progress'),('completed','Completed'),('overdue','Overdue')], default='pending')
    assigned_to = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'legal_compliance'; app_label = 'workspace'

class RegulatoryFiling(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    filing_type = models.CharField(max_length=50)
    regulator = models.CharField(max_length=100)
    period = models.CharField(max_length=20)
    due_date = models.DateField()
    filed_date = models.DateField(null=True)
    status = models.CharField(max_length=20, default=r'pending')
    document_cid = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'legal_filing'; app_label = 'workspace'

class RiskAssessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    risk_type = models.CharField(max_length=50)
    likelihood = models.PositiveSmallIntegerField(choices=[(i,i) for i in range(1,6)])
    impact = models.PositiveSmallIntegerField(choices=[(i,i) for i in range(1,6)])
    risk_score = models.PositiveSmallIntegerField()
    mitigation = models.TextField()
    status = models.CharField(max_length=20, default=r'open')
    assessed_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'legal_risk'; app_label = 'workspace'

class DataPrivacyRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    data_subject = models.CharField(max_length=100)
    data_type = models.CharField(max_length=50)
    purpose = models.TextField()
    legal_basis = models.CharField(max_length=50)
    retention_period = models.PositiveSmallIntegerField()
    is_sensitive = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'legal_privacy'; app_label = 'workspace'

class DataBreachRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    description = models.TextField()
    affected_records = models.PositiveIntegerField(default=0)
    severity = models.CharField(max_length=20)
    reported_to_authority = models.BooleanField(default=False)
    reported_at = models.DateTimeField(null=True)
    resolved_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'legal_breach'; app_label = 'workspace'

class ConsentRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=50)
    consent_type = models.CharField(max_length=50)
    granted = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True)
    class Meta: db_table = r'legal_consent'; app_label = 'workspace'

class AuditFinding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    audit_type = models.CharField(max_length=50)
    finding = models.TextField()
    severity = models.CharField(max_length=20)
    recommendation = models.TextField()
    status = models.CharField(max_length=20, default=r'open')
    due_date = models.DateField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'legal_finding'; app_label = 'workspace'

class PolicyViolation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    employee_id = models.CharField(max_length=50)
    policy = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=20)
    action_taken = models.TextField(blank=True)
    status = models.CharField(max_length=20, default=r'open')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'legal_violation'; app_label = 'workspace'

class LicenseTracking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    software_name = models.CharField(max_length=100)
    license_type = models.CharField(max_length=50)
    seats = models.PositiveIntegerField(default=1)
    used_seats = models.PositiveIntegerField(default=0)
    cost = models.DecimalField(max_digits=15, decimal_places=2)
    expiry_date = models.DateField(null=True)
    vendor = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'legal_license'; app_label = 'workspace'

class ContractManagement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    party_name = models.CharField(max_length=100)
    contract_type = models.CharField(max_length=50)
    value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    auto_renew = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default=r'active')
    document_cid = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'legal_contract'; app_label = 'workspace'

class EthicsComplaint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    complaint_type = models.CharField(max_length=50)
    description = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    reporter_id = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, default=r'open')
    assigned_to = models.CharField(max_length=50, blank=True)
    resolved_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'legal_ethics'; app_label = 'workspace'

class InsiderThreatLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    user_id = models.CharField(max_length=50)
    activity = models.TextField()
    risk_score = models.FloatField(default=0)
    flagged = models.BooleanField(default=False)
    reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'legal_insider'; app_label = 'workspace'

class ComplianceTraining(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField()
    required_for = models.JSONField(default=list)
    due_date = models.DateField(null=True)
    is_mandatory = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'legal_training'; app_label = 'workspace'

class ComplianceTrainingRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    training = models.ForeignKey(ComplianceTraining, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=50)
    completed_at = models.DateTimeField(null=True)
    score = models.FloatField(null=True)
    passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'legal_training_record'; app_label = 'workspace'



# ─── DB_16: Additional Tables (14 tables) ────────────────────────────────────

class ProjectMilestoneV2(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=[(r'pending','Pending'),('completed','Completed'),('overdue','Overdue')], default='pending')
    completed_at = models.DateTimeField(null=True)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'proj_milestone_v2'; app_label = 'workspace'

class ProjectBudgetV2(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    allocated = models.DecimalField(max_digits=15, decimal_places=2)
    spent = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    remaining = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default=r'IDR')
    period = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'proj_budget_v2'; app_label = 'workspace'

class TeamMeeting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    agenda = models.TextField(blank=True)
    meeting_date = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    location = models.CharField(max_length=255, blank=True)
    meeting_url = models.URLField(blank=True)
    minutes = models.TextField(blank=True)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'team_meeting'; app_label = 'workspace'

class MeetingAttendee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(TeamMeeting, on_delete=models.CASCADE, related_name=r'attendees')
    user_id = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[(r'invited','Invited'),('accepted','Accepted'),('declined','Declined'),('attended','Attended')], default='invited')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'team_meeting_attendee'; app_label = 'workspace'

class ActionItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(TeamMeeting, on_delete=models.CASCADE, related_name=r'action_items')
    description = models.TextField()
    assigned_to = models.CharField(max_length=50)
    due_date = models.DateField(null=True)
    status = models.CharField(max_length=20, default=r'pending')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'team_action'; app_label = 'workspace'

class KnowledgeTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default=r'#6366f1')
    usage_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'km_tag'; app_label = 'workspace'

class SystemConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    key = models.CharField(max_length=100)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_secret = models.BooleanField(default=False)
    updated_by = models.CharField(max_length=50)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = r'sys_config'; app_label = 'workspace'

class APIKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    key_hash = models.CharField(max_length=64)
    prefix = models.CharField(max_length=8)
    permissions = models.JSONField(default=list)
    last_used = models.DateTimeField(null=True)
    expires_at = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'sys_api_key'; app_label = 'workspace'

class SystemHealth(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    response_time_ms = models.PositiveIntegerField(default=0)
    cpu_usage = models.FloatField(default=0)
    memory_usage = models.FloatField(default=0)
    disk_usage = models.FloatField(default=0)
    checked_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'sys_health'; app_label = 'workspace'

class NotificationTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    event_type = models.CharField(max_length=50)
    title_template = models.CharField(max_length=255)
    body_template = models.TextField()
    channels = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'notif_template'; app_label = 'workspace'

class UserFeedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=50)
    workspace_id = models.CharField(max_length=50)
    category = models.CharField(max_length=50, choices=[(r'bug','Bug'),('feature','Feature Request'),('improvement','Improvement'),('other','Other')])
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, default=r'open')
    priority = models.CharField(max_length=20, default=r'medium')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'sys_feedback'; app_label = 'workspace'

class AppVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.CharField(max_length=20)
    release_notes = models.TextField()
    is_forced_update = models.BooleanField(default=False)
    min_supported_version = models.CharField(max_length=20)
    released_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'sys_version'; app_label = 'workspace'

class MaintenanceWindow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    affected_services = models.JSONField(default=list)
    status = models.CharField(max_length=20, default=r'scheduled')
    created_by = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'sys_maintenance'; app_label = 'workspace'

class GeoLocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField()
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'sys_geo'; app_label = 'workspace'

