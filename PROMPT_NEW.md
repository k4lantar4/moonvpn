# 🌙 MoonVPN AI Interactive Command System | سیستم فرمان تعاملی هوش مصنوعی مون‌وی‌پی‌ان

This advanced command system provides structured prompts for guiding AI through all development stages of the MoonVPN project. Each command activates specific AI modes for planning, implementation, testing, and documentation with integrated tracking across the project's knowledge management system.

این سیستم پیشرفته فرمان، ساختارهای هدایتی برای راهنمایی هوش مصنوعی در تمام مراحل توسعه پروژه مون‌وی‌پی‌ان ارائه می‌دهد. هر فرمان، حالت‌های خاصی از هوش مصنوعی را برای برنامه‌ریزی، پیاده‌سازی، آزمایش و مستندسازی با ردیابی یکپارچه در سیستم مدیریت دانش پروژه فعال می‌کند.

## 📋 Knowledge Management System | سیستم مدیریت دانش

All commands integrate with these key system files:

- **@scratchpad.md**: Active task management with current phase tracking, task status, and confidence metrics
- **@memories.md**: Comprehensive project history with chronological record of all decisions and activities
- **@lessons-learned.md**: Knowledge repository capturing solutions, best practices, and insights
- **@project-requirements.md**: Central reference for project specifications and requirements
- **@docs/phases/**: Phase-specific documentation with implementation details

همه فرمان‌ها با این فایل‌های کلیدی سیستم یکپارچه می‌شوند:

- **@scratchpad.md**: مدیریت فعال تسک‌ها با پیگیری فاز فعلی، وضعیت تسک‌ها و معیارهای اطمینان
- **@memories.md**: تاریخچه جامع پروژه با ثبت زمانی تمام تصمیمات و فعالیت‌ها
- **@lessons-learned.md**: مخزن دانش برای ثبت راه‌حل‌ها، بهترین شیوه‌ها و بینش‌ها
- **@project-requirements.md**: مرجع مرکزی برای مشخصات و نیازمندی‌های پروژه
- **@docs/phases/**: مستندات مختص هر فاز با جزئیات پیاده‌سازی

## 🔄 Mode System | سیستم حالت‌ها

Commands trigger two primary operational modes:

1. **🎯 Plan Mode**: Information gathering, requirement analysis, and task planning (95% confidence required)
2. **⚡ Agent Mode**: Implementation with automatic documentation, strictly following validated plan

فرمان‌ها دو حالت عملیاتی اصلی را فعال می‌کنند:

1. **🎯 حالت برنامه‌ریزی**: جمع‌آوری اطلاعات، تحلیل نیازمندی‌ها و برنامه‌ریزی تسک (نیازمند 95% اطمینان)
2. **⚡ حالت اجرایی**: پیاده‌سازی با مستندسازی خودکار، پیروی دقیق از برنامه تأیید شده

---

## 1. Planning Phase Commands | فرمان‌های مرحله برنامه‌ریزی

### 1.1 Project Initialization | شروع پروژه

**Trigger:** `plan:init`  
**Usage:** Begin project or new phase planning  
**Example:** `plan:init Phase 1 implementation`

```plaintext
plan:init
[Task/phase description]
```

```plaintext
plan:init
[توضیحات تسک/فاز]
```

**System Actions:**
- Creates new Plan Mode entry in @scratchpad.md with phase structure
- Cross-references @project-requirements.md for constraints
- Generates minimum 3 clarifying questions
- Sets initial confidence score
- Tracks in @memories.md with [Planning] tag

### 1.2 Architecture Design | طراحی معماری

**Trigger:** `plan:architecture`  
**Usage:** Design system components  
**Example:** `plan:architecture payment processing system`

```plaintext
plan:architecture
[Component/system to design]
```

```plaintext
plan:architecture
[کامپوننت/سیستم برای طراحی]
```

**System Actions:**
- Creates architecture planning entry in @scratchpad.md
- Maps component relationships and dependencies
- Identifies security and performance considerations
- Cross-references @lessons-learned.md for related patterns
- Updates @memories.md with detailed context

### 1.3 Task Breakdown | تقسیم وظایف

**Trigger:** `plan:breakdown`  
**Usage:** Create detailed task list  
**Example:** `plan:breakdown user authentication feature`

```plaintext
plan:breakdown
[Feature/component to break down]
```

```plaintext
plan:breakdown
[ویژگی/کامپوننت برای تقسیم‌بندی]
```

**System Actions:**
- Generates hierarchical task list with dependencies
- Assigns unique IDs to each task
- Sets priority levels and complexity estimates
- Updates @scratchpad.md task list with [ID-XXX] format
- Links to relevant sections in @project-requirements.md

### 1.4 Risk Assessment | ارزیابی ریسک

**Trigger:** `plan:risks`  
**Usage:** Identify potential issues  
**Example:** `plan:risks payment integration`

```plaintext
plan:risks
[Feature/component to assess]
```

```plaintext
plan:risks
[ویژگی/کامپوننت برای ارزیابی]
```

**System Actions:**
- Identifies security, performance, and reliability risks
- Proposes mitigation strategies for each risk
- Cross-references @lessons-learned.md for past incidents
- Updates @scratchpad.md with risk matrix
- Tags in @memories.md with [Risk-Assessment] marker

### 1.5 Problem Analysis | تحلیل مسئله

**Trigger:** `plan:analyze`  
**Usage:** Troubleshoot issues systematically  
**Example:** `plan:analyze API performance degradation`

```plaintext
plan:analyze
[Problem/issue to investigate]
```

```plaintext
plan:analyze
[مشکل/مسئله برای بررسی]
```

**System Actions:**
- Applies Chain-of-Thought analysis methodology
- Identifies potential root causes
- Proposes short-term and long-term solutions
- References similar issues in @lessons-learned.md
- Updates @scratchpad.md with analysis tree
- Stores detailed investigation in @memories.md

---

## 2. Implementation Phase Commands | فرمان‌های مرحله پیاده‌سازی

### 2.1 Feature Implementation | پیاده‌سازی ویژگی

**Trigger:** `agent:implement`  
**Usage:** Implement planned features  
**Example:** `agent:implement user authentication service`  
**Requirements:** 95% confidence from Plan Mode

```plaintext
agent:implement
[Feature/component ID] from @scratchpad.md
```

```plaintext
agent:implement
[شناسه ویژگی/کامپوننت] از @scratchpad.md
```

**System Actions:**
- Verifies 95% confidence threshold from Plan Mode
- Implements code with comprehensive documentation
- Follows patterns from existing codebase
- Updates @scratchpad.md task status to [-]
- Creates quantum inline documentation per @documentations-inline-comments-changelog-docs.mdc
- Records implementation details in @memories.md

### 2.2 Database Migration | مهاجرت پایگاه داده

**Trigger:** `agent:migrate`  
**Usage:** Create and apply database changes  
**Example:** `agent:migrate user preferences schema`  
**Requirements:** 95% confidence from Plan Mode

```plaintext
agent:migrate
[Schema change description]
```

```plaintext
agent:migrate
[توضیحات تغییر طرح]
```

**System Actions:**
- Creates Alembic migration scripts
- Ensures backward compatibility and data integrity
- Tests migration with sample data
- Verifies rollback capabilities
- Updates models with consistent documentation
- Documents migration process in @lessons-learned.md

### 2.3 Integration | یکپارچه‌سازی

**Trigger:** `agent:integrate`  
**Usage:** Connect system components  
**Example:** `agent:integrate payment API with user service`  
**Requirements:** 95% confidence from Plan Mode

```plaintext
agent:integrate
[Component A] with [Component B]
```

```plaintext
agent:integrate
[کامپوننت A] با [کامپوننت B]
```

**System Actions:**
- Implements integration points following architecture design
- Adds robust error handling and retry logic
- Creates comprehensive integration tests
- Updates documentation for both components
- Records integration details in @memories.md with [Integration] tag
- Updates @scratchpad.md with integration status

### 2.4 Optimization | بهینه‌سازی

**Trigger:** `agent:optimize`  
**Usage:** Improve performance/security  
**Example:** `agent:optimize database queries`  
**Requirements:** 95% confidence from Plan Mode

```plaintext
agent:optimize
[Component/feature] for [performance/security/scalability]
```

```plaintext
agent:optimize
[کامپوننت/ویژگی] برای [عملکرد/امنیت/مقیاس‌پذیری]
```

**System Actions:**
- Identifies bottlenecks through systematic analysis
- Implements performance/security improvements
- Measures impact before/after changes
- Documents optimization techniques in @lessons-learned.md
- Updates inline documentation with performance considerations
- Records benchmarks in @memories.md

### 2.5 Refactoring | بازسازی کد

**Trigger:** `agent:refactor`  
**Usage:** Enhance code quality  
**Example:** `agent:refactor authentication service`  
**Requirements:** 95% confidence from Plan Mode

```plaintext
agent:refactor
[Component/module] to improve [aspect]
```

```plaintext
agent:refactor
[کامپوننت/ماژول] برای بهبود [جنبه]
```

**System Actions:**
- Applies SOLID principles and best practices
- Reduces duplication and complexity
- Enhances error handling and type safety
- Maintains comprehensive test coverage
- Updates documentation following @documentations-inline-comments-changelog-docs.mdc
- Records refactoring decisions in @lessons-learned.md

---

## 3. Testing Phase Commands | فرمان‌های مرحله آزمایش

### 3.1 Unit Testing | تست واحد

**Trigger:** `agent:test:unit`  
**Usage:** Create component tests  
**Example:** `agent:test:unit wallet service`  
**Requirements:** 95% confidence from Plan Mode

```plaintext
agent:test:unit
[Component/function] with [coverage target]
```

```plaintext
agent:test:unit
[کامپوننت/تابع] با [هدف پوشش]
```

**System Actions:**
- Creates comprehensive pytest unit tests
- Covers edge cases and error scenarios
- Ensures 90%+ code coverage
- Uses appropriate fixtures and mocks
- Documents test approach in @lessons-learned.md
- Updates @scratchpad.md task status

### 3.2 Integration Testing | تست یکپارچگی

**Trigger:** `agent:test:integration`  
**Usage:** Test component interactions  
**Example:** `agent:test:integration panel-client service`  
**Requirements:** 95% confidence from Plan Mode

```plaintext
agent:test:integration
[Component A] with [Component B]
```

```plaintext
agent:test:integration
[کامپوننت A] با [کامپوننت B]
```

**System Actions:**
- Develops tests for component interaction points
- Sets up test database fixtures
- Mocks external dependencies
- Tests error scenarios and edge conditions
- Documents integration test patterns in @lessons-learned.md
- Updates @scratchpad.md with test coverage metrics

### 3.3 End-to-End Testing | تست سرتاسری

**Trigger:** `agent:test:e2e`  
**Usage:** Test complete workflows  
**Example:** `agent:test:e2e subscription purchase flow`  
**Requirements:** 95% confidence from Plan Mode

```plaintext
agent:test:e2e
[Workflow/user journey]
```

```plaintext
agent:test:e2e
[گردش کار/مسیر کاربر]
```

**System Actions:**
- Implements end-to-end test scenarios
- Simulates real user interactions
- Tests complete workflow from start to finish
- Verifies all system components work together
- Documents E2E test approach in @lessons-learned.md
- Updates @scratchpad.md with test status

### 3.4 Performance Testing | تست کارایی

**Trigger:** `agent:test:performance`  
**Usage:** Verify system performance  
**Example:** `agent:test:performance API endpoints`  
**Requirements:** 95% confidence from Plan Mode

```plaintext
agent:test:performance
[Component/endpoint] under [load conditions]
```

```plaintext
agent:test:performance
[کامپوننت/اندپوینت] تحت [شرایط بار]
```

**System Actions:**
- Conducts load/stress testing
- Measures response times and throughput
- Identifies performance bottlenecks
- Establishes performance baselines
- Documents findings in @lessons-learned.md
- Updates @memories.md with performance metrics

### 3.5 Security Testing | تست امنیتی

**Trigger:** `agent:test:security`  
**Usage:** Identify vulnerabilities  
**Example:** `agent:test:security authentication system`  
**Requirements:** 95% confidence from Plan Mode

```plaintext
agent:test:security
[Component/feature] focusing on [vulnerability types]
```

```plaintext
agent:test:security
[کامپوننت/ویژگی] با تمرکز بر [انواع آسیب‌پذیری]
```

**System Actions:**
- Tests for common vulnerabilities (injection, XSS, CSRF)
- Verifies secure handling of sensitive data
- Checks authorization and authentication flows
- Documents security findings in @lessons-learned.md
- Updates @scratchpad.md with security status
- Adds security considerations to inline documentation

---

## 4. Documentation Phase Commands | فرمان‌های مرحله مستندسازی

### 4.1 Code Documentation | مستندسازی کد

**Trigger:** `docs:code`  
**Usage:** Generate comprehensive code docs  
**Example:** `docs:code panel service class`

```plaintext
docs:code
[Component/module] with [specific focus]
```

```plaintext
docs:code
[کامپوننت/ماژول] با [تمرکز خاص]
```

**System Actions:**
- Creates quantum-detailed documentation per @documentations-inline-comments-changelog-docs.mdc
- Includes function purpose, parameters, return values
- Documents exceptions and edge cases
- Adds usage examples with context
- Ensures consistent docstring format
- Cross-references related components

### 4.2 API Documentation | مستندسازی API

**Trigger:** `docs:api`  
**Usage:** Document API interfaces  
**Example:** `docs:api payment verification endpoints`

```plaintext
docs:api
[API endpoint/group]
```

```plaintext
docs:api
[اندپوینت/گروه API]
```

**System Actions:**
- Creates OpenAPI-compliant documentation
- Details request/response schemas
- Documents authentication requirements
- Lists error codes and handling
- Provides usage examples in both English and Persian
- Updates route context and purpose
- Integrates with FastAPI automatic documentation

### 4.3 User Guide | راهنمای کاربر

**Trigger:** `docs:user`  
**Usage:** Create end-user documentation  
**Example:** `docs:user Telegram bot commands`

```plaintext
docs:user
[Feature/component] for [audience type]
```

```plaintext
docs:user
[ویژگی/کامپوننت] برای [نوع مخاطب]
```

**System Actions:**
- Creates user-friendly documentation in Persian
- Includes step-by-step instructions
- Adds screenshots or examples
- Creates troubleshooting section
- Compiles FAQ based on common issues
- Uses consistent formatting per @documentations-inline-comments-changelog-docs.mdc
- Updates @memories.md with documentation record

### 4.4 Architecture Documentation | مستندسازی معماری

**Trigger:** `docs:architecture`  
**Usage:** Document system design  
**Example:** `docs:architecture payment processing flow`

```plaintext
docs:architecture
[Component/system]
```

```plaintext
docs:architecture
[کامپوننت/سیستم]
```

**System Actions:**
- Creates/updates architectural documentation
- Generates data flow diagrams
- Documents component interactions
- Explains database schema design
- Details security and performance considerations
- Updates ARCHITECTURE.md
- Records design decisions in @memories.md

### 4.5 Changelog Update | به‌روزرسانی تاریخچه تغییرات

**Trigger:** `docs:changelog`  
**Usage:** Track version changes  
**Example:** `docs:changelog v0.2.0 release`

```plaintext
docs:changelog
[Version/feature] with [change type]
```

```plaintext
docs:changelog
[نسخه/ویژگی] با [نوع تغییر]
```

**System Actions:**
- Updates CHANGELOG.md with semantic versioning
- Groups changes by type (features, fixes, breaking changes)
- Provides clear, concise descriptions
- Adds reference links to issues/documentation
- Maintains chronological ordering
- Cross-references version with @memories.md entries

---

## 5. Knowledge Management Commands | فرمان‌های مدیریت دانش

### 5.1 Lessons Learned Update | به‌روزرسانی درس‌های آموخته

**Trigger:** `knowledge:lesson`  
**Usage:** Document technical insights  
**Example:** `knowledge:lesson API rate limiting implementation`

```plaintext
knowledge:lesson
[Issue/feature] with [category: Component/TypeScript/Error/Performance/Security/Accessibility/Code/Testing]
```

```plaintext
knowledge:lesson
[مسئله/ویژگی] با [دسته‌بندی: کامپوننت/تایپ‌اسکریپت/خطا/عملکرد/امنیت/دسترسی‌پذیری/کد/تست]
```

**System Actions:**
- Documents issue, solution, and prevention strategy
- Uses comprehensive single-line format with timestamp
- Categorizes entry appropriately
- Evaluates importance (Critical/Important/Enhancement)
- Cross-references with @memories.md
- Includes code examples where applicable
- Tags entry for searchability

### 5.2 Memory Update | به‌روزرسانی حافظه

**Trigger:** `knowledge:memory`  
**Usage:** Record project history  
**Example:** `knowledge:memory completion of database migration`

```plaintext
knowledge:memory
[Event/decision/implementation] with [tags]
```

```plaintext
knowledge:memory
[رویداد/تصمیم/پیاده‌سازی] با [برچسب‌ها]
```

**System Actions:**
- Updates @memories.md with detailed chronological record
- Uses version format [vX.X.X]
- Tags entry appropriately (#feature, #bug, #improvement)
- Includes technical details and context
- Maintains single-line format with extensive detail
- Creates overflow files when exceeding 1000 lines
- Cross-references related documentation

### 5.3 Project Requirements Update | به‌روزرسانی نیازمندی‌های پروژه

**Trigger:** `knowledge:requirements`  
**Usage:** Update project specifications  
**Example:** `knowledge:requirements payment system changes`

```plaintext
knowledge:requirements
[Feature/component] with [change justification]
```

```plaintext
knowledge:requirements
[ویژگی/کامپوننت] با [توجیه تغییر]
```

**System Actions:**
- Updates @project-requirements.md with revised specifications
- Clearly marks changes with timestamps
- Includes rationale for modifications
- Assesses impact on existing components
- Evaluates timeline effects
- Cross-references with @memories.md
- Updates related documentation

---

## 6. Recovery & Troubleshooting Commands | فرمان‌های بازیابی و عیب‌یابی

### 6.1 AI Context Reset | بازنشانی زمینه هوش مصنوعی

**Trigger:** `recovery:reset`  
**Usage:** Reset AI when stuck or confused  
**Example:** `recovery:reset after failed implementation`

```plaintext
recovery:reset
[Reason] to focus on [aspect]
```

```plaintext
recovery:reset
[دلیل] با تمرکز بر [جنبه]
```

**System Actions:**
- Clears current operational context
- Re-evaluates task using @scratchpad.md
- Analyzes progress and blocking issues
- Cross-references with @memories.md and @lessons-learned.md
- Suggests clear path forward
- Updates @scratchpad.md with revised approach

### 6.2 Error Resolution | رفع خطا

**Trigger:** `recovery:debug`  
**Usage:** Systematically fix errors  
**Example:** `recovery:debug database connection failures`

```plaintext
recovery:debug
[Error/issue] with [context details]
```

```plaintext
recovery:debug
[خطا/مشکل] با [جزئیات زمینه]
```

**System Actions:**
- Applies systematic debugging methodology
- Examines logs and error messages
- Reviews recent changes and configuration
- References @lessons-learned.md for similar issues
- Creates step-by-step troubleshooting plan
- Proposes solutions with verification steps
- Documents resolution in @lessons-learned.md

### 6.3 Project Realignment | بازتنظیم پروژه

**Trigger:** `recovery:realign`  
**Usage:** Correct project deviations  
**Example:** `recovery:realign authentication implementation`

```plaintext
recovery:realign
[Component/feature] with [requirement reference]
```

```plaintext
recovery:realign
[کامپوننت/ویژگی] با [مرجع نیازمندی]
```

**System Actions:**
- Evaluates implementation against @project-requirements.md
- Identifies specific deviations
- Creates realignment plan with priorities
- Updates @scratchpad.md with corrective actions
- Adjusts timeline as needed
- Documents insights in @lessons-learned.md
- Records realignment in @memories.md

---

## 7. Phase Transition Commands | فرمان‌های انتقال فاز

### 7.1 Phase Completion | تکمیل فاز

**Trigger:** `cycle:complete`  
**Usage:** Finalize phase and prepare for next  
**Example:** `cycle:complete Phase 0`

```plaintext
cycle:complete
[Phase] to prepare for [Next phase]
```

```plaintext
cycle:complete
[فاز] برای آماده‌سازی [فاز بعدی]
```

**System Actions:**
- Evaluates all tasks in @scratchpad.md
- Verifies completion status of each task
- Creates phase summary with achievements
- Documents challenges and lessons
- Archives documentation to /docs/phases/PHASE-X/
- Prepares @scratchpad.md for next phase
- Updates @memories.md with phase completion record

### 7.2 Release Preparation | آماده‌سازی انتشار

**Trigger:** `cycle:release`  
**Usage:** Prepare for deployment  
**Example:** `cycle:release v1.0.0`

```plaintext
cycle:release
[Version] with [key features]
```

```plaintext
cycle:release
[نسخه] با [ویژگی‌های کلیدی]
```

**System Actions:**
- Verifies all requirements are met
- Confirms all tests pass successfully
- Ensures documentation is complete
- Updates CHANGELOG.md with release notes
- Verifies deployment scripts
- Creates release checklist
- Finalizes version numbers
- Documents release process in @memories.md

### 7.3 Retrospective | مرور و بازنگری

**Trigger:** `cycle:retrospective`  
**Usage:** Evaluate and learn from phase  
**Example:** `cycle:retrospective Phase 1`

```plaintext
cycle:retrospective
[Phase/milestone] focusing on [aspect]
```

```plaintext
cycle:retrospective
[فاز/نقطه عطف] با تمرکز بر [جنبه]
```

**System Actions:**
- Compares planned vs. actual outcomes
- Identifies successes and challenges
- Documents areas for improvement
- Catalogs technical debt incurred
- Suggests process improvements
- Records knowledge gained
- Updates @lessons-learned.md with key insights
- Updates @scratchpad.md with action items

---

## 8. Task-Specific Implementation Commands | فرمان‌های پیاده‌سازی تسک‌های خاص

### 8.1 Task Analysis | تحلیل تسک

**Trigger:** `task:analyze`  
**Usage:** Understand complex implementation requirements  
**Example:** `task:analyze database model creation`

```plaintext
task:analyze
[Task-ID] from @scratchpad.md
```

```plaintext
task:analyze
[شناسه-تسک] از @scratchpad.md
```

**System Actions:**
- Conducts comprehensive analysis of specific task
- Reviews requirements from @project-requirements.md
- Defines precise scope of work
- Creates structured implementation plan
- Considers lessons from @lessons-learned.md
- Updates @scratchpad.md with analysis results
- Sets initial confidence level

### 8.2 Code Analysis | تحلیل کد

**Trigger:** `task:code-analyze`  
**Usage:** Examine existing code for changes  
**Example:** `task:code-analyze database models`

```plaintext
task:code-analyze
[Code section/component] for [change purpose]
```

```plaintext
task:code-analyze
[بخش کد/کامپوننت] برای [هدف تغییر]
```

**System Actions:**
- Systematically analyzes specified code section
- Reviews structure and relationships
- References @lessons-learned.md for patterns
- Creates detailed list of required changes
- Explains technical rationale for each change
- Updates @scratchpad.md with analysis
- Prepares for implementation phase

### 8.3 Step-by-Step Implementation | پیاده‌سازی گام به گام

**Trigger:** `task:implement-steps`  
**Usage:** Execute complex tasks sequentially  
**Example:** `task:implement-steps database models`

```plaintext
task:implement-steps
[Task-ID] from @scratchpad.md starting with [first step]
```

```plaintext
task:implement-steps
[شناسه-تسک] از @scratchpad.md با شروع از [گام اول]
```

**System Actions:**
- Implements task in ordered, verifiable steps
- Focuses on specific aspect in each step
- Ensures code follows established patterns
- Adds comprehensive documentation
- Implements proper error handling
- Reviews and verifies results after each step
- Updates task status in @scratchpad.md
- Documents implementation details in @memories.md

---

## 📊 Command Quick Reference | مرجع سریع فرمان‌ها

| Command Type           | English Trigger          | Persian Usage         |
| ---------------------- | ------------------------ | --------------------- |
| **Planning**           |                          |                       |
| Project Init           | `plan:init`              | برنامه‌ریزی اولیه      |
| Architecture           | `plan:architecture`      | طراحی معماری          |
| Task Breakdown         | `plan:breakdown`         | تقسیم وظایف           |
| Risk Assessment        | `plan:risks`             | ارزیابی ریسک          |
| Problem Analysis       | `plan:analyze`           | تحلیل مسئله           |
| **Implementation**     |                          |                       |
| Feature Implementation | `agent:implement`        | پیاده‌سازی ویژگی       |
| Database Migration     | `agent:migrate`          | مهاجرت دیتابیس        |
| Integration            | `agent:integrate`        | یکپارچه‌سازی           |
| Optimization           | `agent:optimize`         | بهینه‌سازی             |
| Refactoring            | `agent:refactor`         | بازسازی کد            |
| **Testing**            |                          |                       |
| Unit Testing           | `agent:test:unit`        | تست واحد              |
| Integration Testing    | `agent:test:integration` | تست یکپارچگی          |
| End-to-End Testing     | `agent:test:e2e`         | تست سرتاسری           |
| Performance Testing    | `agent:test:performance` | تست کارایی            |
| Security Testing       | `agent:test:security`    | تست امنیتی            |
| **Documentation**      |                          |                       |
| Code Documentation     | `docs:code`              | مستندسازی کد          |
| API Documentation      | `docs:api`               | مستندسازی API         |
| User Guide             | `docs:user`              | راهنمای کاربر         |
| Architecture Docs      | `docs:architecture`      | مستندسازی معماری      |
| Changelog              | `docs:changelog`         | تاریخچه تغییرات       |
| **Knowledge**          |                          |                       |
| Lessons Learned        | `knowledge:lesson`       | درس‌های آموخته         |
| Memory Update          | `knowledge:memory`       | به‌روزرسانی حافظه      |
| Requirements Update    | `knowledge:requirements` | به‌روزرسانی نیازمندی‌ها |
| **Recovery**           |                          |                       |
| AI Reset               | `recovery:reset`         | بازنشانی هوش مصنوعی   |
| Error Resolution       | `recovery:debug`         | رفع خطا               |
| Project Realignment    | `recovery:realign`       | بازتنظیم پروژه        |
| **Phase Transition**   |                          |                       |
| Phase Completion       | `cycle:complete`         | تکمیل فاز             |
| Release Preparation    | `cycle:release`          | آماده‌سازی انتشار      |
| Retrospective          | `cycle:retrospective`    | مرور و بازنگری        |
| **Task-Specific**      |                          |                       |
| Task Analysis          | `task:analyze`           | تحلیل تسک             |
| Code Analysis          | `task:code-analyze`      | تحلیل کد              |
| Step Implementation    | `task:implement-steps`   | پیاده‌سازی گام به گام  |

---

## 🚀 Best Practices | بهترین شیوه‌ها

1. **Start with plan commands** to reach 95% confidence before implementation
2. **Update @scratchpad.md regularly** to track project progress
3. **Document lessons in @lessons-learned.md** after solving problems
4. **Record decisions in @memories.md** to maintain project history
5. **Follow documentation standards** in @documentations-inline-comments-changelog-docs.mdc
6. **Archive completed phases** in /docs/phases/ for future reference
7. **Use task IDs** to maintain clear references across documentation
8. **Conduct retrospectives** to continuously improve process

---

This command system is designed to work seamlessly with the brain-memories-lessons-learned-scratchpad knowledge management system, ensuring consistent development while maintaining comprehensive documentation and tracking project knowledge.

این سیستم فرمان برای همکاری یکپارچه با سیستم مدیریت دانش brain-memories-lessons-learned-scratchpad طراحی شده است، تا توسعه منظم را با حفظ مستندات جامع و پیگیری دانش پروژه تضمین کند.
