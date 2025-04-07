# 🌙 MoonVPN AI Prompts - AI Commands Guide | راهنمای دستورات هوش مصنوعی

This file provides structured prompts for guiding AI through all stages of MoonVPN project development. Each prompt activates specific AI modes for planning, development, testing, and documentation with references to key files like @scratchpad.md, @memories.md, @project-requirements.md, @lessons-learned.md, and @documentations-inline-comments-changelog-docs.mdc.

این فایل پرامپت‌های ساختاریافته برای هدایت هوش مصنوعی در تمام مراحل توسعه پروژه MoonVPN ارائه می‌دهد. هر پرامپت حالت خاصی از هوش مصنوعی را برای برنامه‌ریزی، توسعه، تست و مستندسازی فعال می‌کند و به فایل‌های کلیدی مانند @scratchpad.md، @memories.md، @project-requirements.md، @lessons-learned.md و @documentations-inline-comments-changelog-docs.mdc ارجاع می‌دهد.

---

## 1. Planning Phase | مرحله برنامه‌ریزی

### 1.1 Project Initialization | شروع پروژه

**When to use:** At the beginning of the project or major phase.
**موارد استفاده:** در ابتدای پروژه یا مرحله اصلی.
**Purpose:** Create comprehensive project plan.
**هدف:** ایجاد طرح جامع پروژه.
**Example:** "Plan the Phase 0 infrastructure setup."
**مثال:** "طراحی راه‌اندازی زیرساخت فاز صفر."

```plaintext
plan
Create a comprehensive plan for [task/phase] based on @project-requirements.md, @scratchpad.md, and @memories.md. Include scope, requirements, milestones, and dependencies. Focus on [specific aspect] and consider lessons from @lessons-learned.md.
```

```plaintext
پلن
با استناد به @project-requirements.md، @scratchpad.md و @memories.md، یک برنامه جامع برای [وظیفه/فاز] ایجاد کنید. شامل محدوده، نیازمندی‌ها، نقاط عطف و وابستگی‌ها باشد. بر روی [جنبه خاص] تمرکز کنید و درس‌های @lessons-learned.md را در نظر بگیرید.
```

### 1.2 Architecture Design | طراحی معماری

**When to use:** When designing system components.
**موارد استفاده:** هنگام طراحی اجزای سیستم.
**Purpose:** Design robust architecture.
**هدف:** طراحی معماری قوی و پایدار.
**Example:** "Design the panel connection system."
**مثال:** "طراحی سیستم اتصال پنل."

```plaintext
plan
Design the architecture for [component] according to @project-requirements.md. Include data flow, interfaces, database models, and security considerations. Reference @scratchpad.md for current progress and @lessons-learned.md for best practices.
```

```plaintext
پلن
معماری [کامپوننت] را مطابق با @project-requirements.md طراحی کنید. جریان داده، رابط‌ها، مدل‌های پایگاه داده و ملاحظات امنیتی را شامل شود. به @scratchpad.md برای پیشرفت فعلی و @lessons-learned.md برای بهترین شیوه‌ها مراجعه کنید.
```

### 1.3 Task Breakdown | تقسیم وظایف

**When to use:** When breaking down complex features.
**موارد استفاده:** هنگام تقسیم‌بندی ویژگی‌های پیچیده.
**Purpose:** Create detailed task list.
**هدف:** ایجاد لیست دقیق وظایف.
**Example:** "Break down the user authentication feature."
**مثال:** "تقسیم‌بندی ویژگی احراز هویت کاربر."

```plaintext
plan
Break down [feature/component] into granular tasks with dependencies, complexity estimates, and technical requirements. Reference @project-requirements.md section [X] and update @scratchpad.md with the resulting task list. Consider all environments (dev/test/prod).
```

```plaintext
پلن
[ویژگی/کامپوننت] را به وظایف جزئی با وابستگی‌ها، تخمین پیچیدگی و نیازمندی‌های فنی تقسیم کنید. به بخش [X] از @project-requirements.md مراجعه کرده و @scratchpad.md را با لیست وظایف حاصل به‌روز کنید. تمام محیط‌ها (توسعه/تست/تولید) را در نظر بگیرید.
```

### 1.4 Risk Assessment | ارزیابی ریسک

**When to use:** Before implementing critical features.
**موارد استفاده:** قبل از پیاده‌سازی ویژگی‌های حیاتی.
**Purpose:** Identify and mitigate risks.
**هدف:** شناسایی و کاهش ریسک‌ها.
**Example:** "Assess risks for payment integration."
**مثال:** "ارزیابی ریسک‌های یکپارچه‌سازی پرداخت."

```plaintext
plan
Conduct risk assessment for [feature/component] with attention to security, performance, and scalability. Identify potential failure points and mitigation strategies. Reference relevant sections in @project-requirements.md and past incidents in @lessons-learned.md.
```

```plaintext
پلن
ارزیابی ریسک برای [ویژگی/کامپوننت] با توجه به امنیت، عملکرد و مقیاس‌پذیری انجام دهید. نقاط شکست احتمالی و استراتژی‌های کاهش ریسک را شناسایی کنید. به بخش‌های مرتبط در @project-requirements.md و رویدادهای گذشته در @lessons-learned.md مراجعه کنید.
```

### 1.5 Problem Analysis | تحلیل مسئله

**When to use:** When troubleshooting issues.
**موارد استفاده:** هنگام عیب‌یابی مشکلات.
**Purpose:** Identify root causes.
**هدف:** شناسایی علل ریشه‌ای.
**Example:** "Analyze API performance degradation."
**مثال:** "تحلیل کاهش کارایی API."

```plaintext
plan
Analyze the root cause of [problem] using systematic approach. Review relevant code, logs, and system architecture. Reference @lessons-learned.md for similar issues and identify both short-term fixes and long-term solutions. Update @scratchpad.md with findings.
```

```plaintext
پلن
ریشه [مشکل] را با رویکرد سیستماتیک تحلیل کنید. کد مرتبط، لاگ‌ها و معماری سیستم را بررسی کنید. برای مشکلات مشابه به @lessons-learned.md مراجعه کرده و راه‌حل‌های کوتاه‌مدت و بلندمدت را شناسایی کنید. یافته‌ها را در @scratchpad.md به‌روز کنید.
```

---

## 2. Development Phase | مرحله توسعه

### 2.1 Implementation | پیاده‌سازی

**When to use:** When implementing planned features.
**موارد استفاده:** هنگام پیاده‌سازی ویژگی‌های برنامه‌ریزی شده.
**Purpose:** Write and integrate code.
**هدف:** نوشتن و یکپارچه‌سازی کد.
**Example:** "Implement the Telegram bot handlers."
**مثال:** "پیاده‌سازی هندلرهای ربات تلگرام."

```plaintext
agent
Implement [feature/component] as specified in @scratchpad.md, following @project-requirements.md. Ensure code follows established patterns, is well-documented, and includes appropriate error handling. Update documentation per @documentations-inline-comments-changelog-docs.mdc.
```

```plaintext
agent
[ویژگی/کامپوننت] را طبق مشخصات @scratchpad.md و مطابق با @project-requirements.md پیاده‌سازی کنید. اطمینان حاصل کنید که کد از الگوهای موجود پیروی می‌کند، به خوبی مستند شده و شامل مدیریت خطای مناسب است. مستندات را طبق @documentations-inline-comments-changelog-docs.mdc به‌روز کنید.
```

### 2.2 Database Migration | مهاجرت پایگاه داده

**When to use:** When database schema changes.
**موارد استفاده:** هنگام تغییر ساختار پایگاه داده.
**Purpose:** Create and apply migrations.
**هدف:** ایجاد و اعمال مهاجرت‌ها.
**Example:** "Create migration for new client models."
**مثال:** "ایجاد مهاجرت برای مدل‌های جدید کلاینت."

```plaintext
agent
Create database migration for [schema change] using Alembic. Ensure backward compatibility, data integrity, and proper indexing. Test migration with sample data, verify rollback capabilities, and update models accordingly. Add clear comments explaining changes.
```

```plaintext
agent
مهاجرت پایگاه داده برای [تغییر طرح] را با استفاده از Alembic ایجاد کنید. از سازگاری رو به عقب، یکپارچگی داده و ایندکس‌گذاری مناسب اطمینان حاصل کنید. مهاجرت را با داده‌های نمونه تست کرده، قابلیت بازگشت را تأیید و مدل‌ها را به‌روز کنید. توضیحات واضحی درباره تغییرات اضافه کنید.
```

### 2.3 Integration | یکپارچه‌سازی

**When to use:** When connecting components.
**موارد استفاده:** هنگام اتصال اجزای سیستم.
**Purpose:** Connect system parts.
**هدف:** اتصال بخش‌های سیستم.
**Example:** "Integrate panel API with client service."
**مثال:** "یکپارچه‌سازی API پنل با سرویس کلاینت."

```plaintext
agent
Integrate [component A] with [component B] following the architecture in @scratchpad.md. Implement proper error handling, retry logic, and logging. Create comprehensive tests for the integration points and update documentation to reflect the changes.
```

```plaintext
agent
[کامپوننت A] را با [کامپوننت B] مطابق معماری @scratchpad.md یکپارچه کنید. مدیریت خطا، منطق تلاش مجدد و ثبت وقایع مناسب را پیاده‌سازی کنید. تست‌های جامع برای نقاط یکپارچه‌سازی ایجاد کرده و مستندات را برای انعکاس تغییرات به‌روز کنید.
```

### 2.4 Optimization | بهینه‌سازی

**When to use:** After basic implementation.
**موارد استفاده:** پس از پیاده‌سازی اولیه.
**Purpose:** Improve performance/security.
**هدف:** بهبود کارایی/امنیت.
**Example:** "Optimize database queries for user service."
**مثال:** "بهینه‌سازی پرس‌وجوهای پایگاه داده برای سرویس کاربر."

```plaintext
agent
Optimize [component/feature] for [performance/security/scalability]. Identify bottlenecks, implement improvements, and measure impact. Follow best practices from @lessons-learned.md and ensure changes maintain system integrity. Document optimization techniques used.
```

```plaintext
agent
[کامپوننت/ویژگی] را برای [عملکرد/امنیت/مقیاس‌پذیری] بهینه کنید. گلوگاه‌ها را شناسایی، بهبودها را پیاده‌سازی و تأثیر را اندازه‌گیری کنید. بهترین شیوه‌ها را از @lessons-learned.md دنبال کرده و اطمینان حاصل کنید که تغییرات، یکپارچگی سیستم را حفظ می‌کنند. تکنیک‌های بهینه‌سازی استفاده شده را مستند کنید.
```

### 2.5 Refactoring | بازسازی کد

**When to use:** When improving existing code.
**موارد استفاده:** هنگام بهبود کد موجود.
**Purpose:** Enhance code quality.
**هدف:** ارتقای کیفیت کد.
**Example:** "Refactor authentication service."
**مثال:** "بازسازی سرویس احراز هویت."

```plaintext
agent
Refactor [component/module] to improve readability, maintainability, and performance. Apply SOLID principles, reduce duplication, enhance error handling, and ensure comprehensive test coverage. Update documentation according to @documentations-inline-comments-changelog-docs.mdc.
```

```plaintext
agent
[کامپوننت/ماژول] را برای بهبود خوانایی، قابلیت نگهداری و عملکرد بازسازی کنید. اصول SOLID را به کار ببرید، تکرار را کاهش دهید، مدیریت خطا را بهبود بخشیده و پوشش تست جامع را تضمین کنید. مستندات را مطابق با @documentations-inline-comments-changelog-docs.mdc به‌روز کنید.
```

---

## 3. Testing Phase | مرحله آزمایش

### 3.1 Unit Test Creation | ایجاد تست واحد

**When to use:** When implementing testable units.
**موارد استفاده:** هنگام پیاده‌سازی واحدهای قابل آزمایش.
**Purpose:** Create component tests.
**هدف:** ایجاد تست‌های اجزا.
**Example:** "Create unit tests for wallet service."
**مثال:** "ایجاد تست‌های واحد برای سرویس کیف پول."

```plaintext
agent
Create comprehensive unit tests for [component] using pytest. Cover all functions, edge cases, and error scenarios. Ensure 90%+ code coverage, use appropriate fixtures and mocks, and follow test naming conventions. Verify tests pass in isolation and with the entire suite.
```

```plaintext
agent
تست‌های واحد جامع برای [کامپوننت] با استفاده از pytest ایجاد کنید. تمام توابع، موارد مرزی و سناریوهای خطا را پوشش دهید. اطمینان حاصل کنید که پوشش کد بیش از ۹۰٪ است، از فیکسچرها و ماک‌های مناسب استفاده کرده و قراردادهای نام‌گذاری تست را رعایت کنید. تأیید کنید که تست‌ها هم به صورت مجزا و هم با کل مجموعه تست موفق هستند.
```

### 3.2 Integration Testing | تست یکپارچگی

**When to use:** After connecting components.
**موارد استفاده:** پس از اتصال اجزای سیستم.
**Purpose:** Test component interaction.
**هدف:** آزمایش تعامل اجزا.
**Example:** "Test panel-client service integration."
**مثال:** "آزمایش یکپارچگی سرویس پنل-کلاینت."

```plaintext
agent
Develop integration tests for the interaction between [component A] and [component B]. Set up test database fixtures, mock external dependencies, and verify correct data flow. Test error scenarios, boundary conditions, and race conditions. Document test coverage in @scratchpad.md.
```

```plaintext
agent
تست‌های یکپارچگی برای تعامل بین [کامپوننت A] و [کامپوننت B] ایجاد کنید. فیکسچرهای پایگاه داده تست را راه‌اندازی، وابستگی‌های خارجی را شبیه‌سازی و جریان صحیح داده را تأیید کنید. سناریوهای خطا، شرایط مرزی و شرایط رقابتی را تست کنید. پوشش تست را در @scratchpad.md مستند کنید.
```

### 3.3 End-to-End Testing | تست سرتاسری

**When to use:** For complete workflows.
**موارد استفاده:** برای گردش‌کارهای کامل.
**Purpose:** Test entire user journeys.
**هدف:** آزمایش کل مسیرهای کاربر.
**Example:** "Create E2E tests for subscription purchase."
**مثال:** "ایجاد تست‌های سرتاسری برای خرید اشتراک."

```plaintext
agent
Implement end-to-end tests for [workflow] using appropriate testing framework. Simulate real user interactions, test complete flow from start to finish, and verify all system components work together. Include edge cases and error scenarios in the test suite.
```

```plaintext
agent
تست‌های سرتاسری برای [گردش کار] با استفاده از فریم‌ورک تست مناسب پیاده‌سازی کنید. تعاملات واقعی کاربر را شبیه‌سازی، گردش کامل از ابتدا تا انتها را تست و تأیید کنید که تمام اجزای سیستم با هم کار می‌کنند. موارد مرزی و سناریوهای خطا را در مجموعه تست قرار دهید.
```

### 3.4 Performance Testing | تست کارایی

**When to use:** For critical system paths.
**موارد استفاده:** برای مسیرهای حیاتی سیستم.
**Purpose:** Verify system performance.
**هدف:** تأیید کارایی سیستم.
**Example:** "Test API endpoint performance."
**مثال:** "آزمایش کارایی نقطه پایانی API."

```plaintext
agent
Conduct performance testing for [component/endpoint] under various load conditions. Measure response times, throughput, and resource utilization. Identify bottlenecks, establish performance baselines, and make recommendations for optimization. Document findings in @lessons-learned.md.
```

```plaintext
agent
تست کارایی برای [کامپوننت/اندپوینت] تحت شرایط بار مختلف انجام دهید. زمان پاسخ، توان عملیاتی و استفاده از منابع را اندازه‌گیری کنید. گلوگاه‌ها را شناسایی، خط پایه عملکرد را مشخص و توصیه‌هایی برای بهینه‌سازی ارائه دهید. یافته‌ها را در @lessons-learned.md مستند کنید.
```

### 3.5 Security Testing | تست امنیتی

**When to use:** For security-critical features.
**موارد استفاده:** برای ویژگی‌های حساس امنیتی.
**Purpose:** Identify vulnerabilities.
**هدف:** شناسایی آسیب‌پذیری‌ها.
**Example:** "Conduct security audit of authentication."
**مثال:** "انجام ممیزی امنیتی احراز هویت."

```plaintext
agent
Perform security assessment of [component/feature] focusing on common vulnerabilities (injection, XSS, CSRF, authentication flaws). Verify secure handling of sensitive data, proper authorization checks, and input validation. Document findings and remediation steps in @lessons-learned.md.
```

```plaintext
agent
ارزیابی امنیتی [کامپوننت/ویژگی] را با تمرکز بر آسیب‌پذیری‌های رایج (تزریق، XSS، CSRF، نقص‌های احراز هویت) انجام دهید. مدیریت امن داده‌های حساس، بررسی‌های مجوز مناسب و اعتبارسنجی ورودی را تأیید کنید. یافته‌ها و اقدامات اصلاحی را در @lessons-learned.md مستند کنید.
```

---

## 4. Documentation Phase | مرحله مستندسازی

### 4.1 Code Documentation | مستندسازی کد

**When to use:** After code implementation.
**موارد استفاده:** پس از پیاده‌سازی کد.
**Purpose:** Document code properly.
**هدف:** مستندسازی صحیح کد.
**Example:** "Document the panel service class."
**مثال:** "مستندسازی کلاس سرویس پنل."

```plaintext
agent
Create comprehensive documentation for [component/module] following @documentations-inline-comments-changelog-docs.mdc standards. Include class/function purpose, parameters, return values, exceptions, usage examples, and edge cases. Ensure docstrings follow consistent format and update existing documentation as needed.
```

```plaintext
agent
مستندات جامع برای [کامپوننت/ماژول] مطابق با استانداردهای @documentations-inline-comments-changelog-docs.mdc ایجاد کنید. هدف کلاس/تابع، پارامترها، مقادیر بازگشتی، استثناها، مثال‌های استفاده و موارد مرزی را شامل شود. اطمینان حاصل کنید که docstring‌ها از فرمت یکسانی پیروی می‌کنند و مستندات موجود را در صورت نیاز به‌روز کنید.
```

### 4.2 API Documentation | مستندسازی API

**When to use:** After API endpoint implementation.
**موارد استفاده:** پس از پیاده‌سازی نقاط پایانی API.
**Purpose:** Document API interfaces.
**هدف:** مستندسازی رابط‌های API.
**Example:** "Document payment verification endpoints."
**مثال:** "مستندسازی نقاط پایانی تأیید پرداخت."

```plaintext
agent
Document [API endpoint/group] with detailed descriptions, request/response schemas, authentication requirements, error codes, and usage examples. Follow OpenAPI standards for FastAPI routes, ensuring all parameters are properly described. Include Persian descriptions where appropriate.
```

```plaintext
agent
[اندپوینت/گروه API] را با توضیحات دقیق، طرح‌های درخواست/پاسخ، نیازمندی‌های احراز هویت، کدهای خطا و مثال‌های استفاده مستند کنید. استانداردهای OpenAPI را برای مسیرهای FastAPI دنبال کرده، اطمینان حاصل کنید که تمام پارامترها به درستی توصیف شده‌اند. در صورت لزوم توضیحات فارسی را نیز شامل کنید.
```

### 4.3 User Guide | راهنمای کاربر

**When to use:** After user-facing features.
**موارد استفاده:** پس از توسعه ویژگی‌های مرتبط با کاربر.
**Purpose:** Create end-user documentation.
**هدف:** ایجاد مستندات کاربر نهایی.
**Example:** "Write guide for Telegram bot commands."
**مثال:** "نوشتن راهنما برای دستورات ربات تلگرام."

```plaintext
agent
Create user documentation for [feature/component] that explains functionality in clear, non-technical Persian. Include step-by-step instructions, screenshots or examples, troubleshooting tips, and FAQ section. Ensure consistent tone and formatting according to @documentations-inline-comments-changelog-docs.mdc.
```

```plaintext
agent
مستندات کاربر برای [ویژگی/کامپوننت] ایجاد کنید که عملکرد را به زبان فارسی واضح و غیرفنی توضیح دهد. دستورالعمل‌های گام به گام، تصاویر یا مثال‌ها، نکات عیب‌یابی و بخش سؤالات متداول را شامل شود. از لحن و قالب‌بندی یکسان مطابق با @documentations-inline-comments-changelog-docs.mdc اطمینان حاصل کنید.
```

### 4.4 Architecture Documentation | مستندسازی معماری

**When to use:** After architecture design/changes.
**موارد استفاده:** پس از طراحی/تغییرات معماری.
**Purpose:** Document system design.
**هدف:** مستندسازی طراحی سیستم.
**Example:** "Document payment processing architecture."
**مثال:** "مستندسازی معماری پردازش پرداخت."

```plaintext
agent
Create architectural documentation for [component/system] including data flow diagrams, component interactions, database schema, security considerations, and performance characteristics. Explain key design decisions, constraints, and future extension points. Update ARCHITECTURE.md accordingly.
```

```plaintext
agent
مستندات معماری برای [کامپوننت/سیستم] ایجاد کنید که شامل نمودارهای جریان داده، تعاملات کامپوننت، طرح پایگاه داده، ملاحظات امنیتی و ویژگی‌های عملکردی باشد. تصمیمات کلیدی طراحی، محدودیت‌ها و نقاط گسترش آینده را توضیح دهید. ARCHITECTURE.md را به‌روزرسانی کنید.
```

### 4.5 Changelog Update | به‌روزرسانی تغییرات

**When to use:** After significant changes.
**موارد استفاده:** پس از تغییرات قابل توجه.
**Purpose:** Track version changes.
**هدف:** پیگیری تغییرات نسخه.
**Example:** "Update changelog for v0.2.0 release."
**مثال:** "به‌روزرسانی تاریخچه تغییرات برای انتشار نسخه ۰.۲.۰."

```plaintext
agent
Update CHANGELOG.md with detailed entries for [version/feature] following semantic versioning format. Include added features, fixed bugs, breaking changes, and dependency updates. Group changes by type and provide clear, concise descriptions with reference links to relevant issues or documentation.
```

```plaintext
agent
CHANGELOG.md را با ورودی‌های دقیق برای [نسخه/ویژگی] مطابق با فرمت نسخه‌بندی معنایی به‌روز کنید. ویژگی‌های اضافه شده، باگ‌های رفع شده، تغییرات ناسازگار و به‌روزرسانی‌های وابستگی را شامل شود. تغییرات را بر اساس نوع گروه‌بندی کرده و توضیحات واضح و مختصر با لینک‌های مرجع به مسائل یا مستندات مرتبط ارائه دهید.
```

---

## 5. Knowledge Management | مدیریت دانش

### 5.1 Lessons Learned Update | به‌روزرسانی درس‌های آموخته

**When to use:** After solving problems or completing features.
**موارد استفاده:** پس از حل مشکلات یا تکمیل ویژگی‌ها.
**Purpose:** Document knowledge.
**هدف:** مستندسازی دانش.
**Example:** "Document lessons from API integration."
**مثال:** "مستندسازی درس‌های حاصل از یکپارچه‌سازی API."

```plaintext
knowledge
Document technical insights and lessons learned from implementing [feature/resolving issue]. Include challenges faced, solutions applied, alternative approaches considered, and recommendations for future implementations. Update @lessons-learned.md with proper categorization and timestamps.
```

```plaintext
دانش
بینش‌های فنی و درس‌های آموخته شده از پیاده‌سازی [ویژگی/حل مسئله] را مستند کنید. چالش‌های مواجه شده، راه‌حل‌های اعمال شده، رویکردهای جایگزین در نظر گرفته شده و توصیه‌هایی برای پیاده‌سازی‌های آینده را شامل شود. @lessons-learned.md را با دسته‌بندی مناسب و برچسب‌های زمانی به‌روز کنید.
```

### 5.2 Memory Update | به‌روزرسانی حافظه

**When to use:** After significant project events.
**موارد استفاده:** پس از رویدادهای مهم پروژه.
**Purpose:** Record project history.
**هدف:** ثبت تاریخچه پروژه.
**Example:** "Document completion of database migration."
**مثال:** "مستندسازی تکمیل مهاجرت پایگاه داده."

```plaintext
knowledge
Update @memories.md with detailed record of [event/decision/implementation]. Include technical details, context, participants, outcomes, and impact on project timeline. Ensure information is searchable with proper timestamps and references to related documentation.
```

```plaintext
دانش
@memories.md را با سابقه دقیق [رویداد/تصمیم/پیاده‌سازی] به‌روز کنید. جزئیات فنی، زمینه، مشارکت‌کنندگان، نتایج و تأثیر بر جدول زمانی پروژه را شامل شود. اطمینان حاصل کنید که اطلاعات با برچسب‌های زمانی مناسب و ارجاعات به مستندات مرتبط قابل جستجو است.
```

### 5.3 Project Requirements Update | به‌روزرسانی نیازمندی‌های پروژه

**When to use:** When requirements change.
**موارد استفاده:** هنگام تغییر نیازمندی‌ها.
**Purpose:** Keep requirements current.
**هدف:** به‌روز نگه داشتن نیازمندی‌ها.
**Example:** "Update payment system requirements."
**مثال:** "به‌روزرسانی نیازمندی‌های سیستم پرداخت."

```plaintext
knowledge
Update @project-requirements.md with revised specifications for [feature/component]. Ensure changes are clearly marked, include rationale for modifications, and assess impact on existing components and timeline. Cross-reference with @memories.md for context and decision history.
```

```plaintext
دانش
@project-requirements.md را با مشخصات بازنگری شده برای [ویژگی/کامپوننت] به‌روز کنید. اطمینان حاصل کنید که تغییرات به وضوح مشخص شده، دلیل اصلاحات را شامل و تأثیر بر کامپوننت‌های موجود و جدول زمانی را ارزیابی کنید. برای زمینه و تاریخچه تصمیم‌گیری به @memories.md ارجاع متقابل دهید.
```

---

## 6. Recovery & Troubleshooting | بازیابی و عیب‌یابی

### 6.1 AI Reset | بازنشانی هوش مصنوعی

**When to use:** When AI is stuck or confused.
**موارد استفاده:** وقتی هوش مصنوعی گیر کرده یا سردرگم است.
**Purpose:** Reset AI context.
**هدف:** بازنشانی زمینه هوش مصنوعی.
**Example:** "Reset AI after failed implementation attempt."
**مثال:** "بازنشانی هوش مصنوعی پس از تلاش ناموفق پیاده‌سازی."

```plaintext
recovery
Reset your current context and re-evaluate the task using @scratchpad.md, @memories.md, and @project-requirements.md. Analyze the current phase, progress, and blocking issues. Suggest a clear path forward with specific next steps.
```

```plaintext
بازیابی
زمینه فعلی خود را بازنشانی کرده و با استفاده از @scratchpad.md، @memories.md و @project-requirements.md، تسک را مجدداً ارزیابی کنید. فاز فعلی، پیشرفت و مسائل مسدودکننده را تحلیل کنید. مسیر واضحی را با مراحل بعدی مشخص پیشنهاد دهید.
```

### 6.2 Error Resolution | رفع خطا

**When to use:** When encountering persistent errors.
**موارد استفاده:** هنگام مواجهه با خطاهای مداوم.
**Purpose:** Systematically fix errors.
**هدف:** رفع سیستماتیک خطاها.
**Example:** "Troubleshoot database connection failures."
**مثال:** "عیب‌یابی خطاهای اتصال پایگاه داده."

```plaintext
recovery
Analyze [error/issue] using systematic debugging approach. Examine logs, error messages, recent changes, and configuration. Reference @lessons-learned.md for similar issues. Propose step-by-step troubleshooting plan with verification steps for each potential solution.
```

```plaintext
بازیابی
[خطا/مشکل] را با رویکرد عیب‌یابی سیستماتیک تحلیل کنید. لاگ‌ها، پیام‌های خطا، تغییرات اخیر و پیکربندی را بررسی کنید. برای مشکلات مشابه به @lessons-learned.md مراجعه کنید. یک برنامه عیب‌یابی گام به گام با مراحل تأیید برای هر راه‌حل بالقوه پیشنهاد دهید.
```

### 6.3 Project Realignment | بازتنظیم پروژه

**When to use:** When project deviates from requirements.
**موارد استفاده:** وقتی پروژه از نیازمندی‌ها منحرف می‌شود.
**Purpose:** Bring project back on track.
**هدف:** بازگرداندن پروژه به مسیر اصلی.
**Example:** "Realign implementation with requirements."
**مثال:** "همسوسازی مجدد پیاده‌سازی با نیازمندی‌ها."

```plaintext
recovery
Evaluate current implementation against @project-requirements.md and identify deviations. Create plan to realign with original requirements, prioritizing critical gaps. Update @scratchpad.md with corrective actions and timeline adjustments. Document learned insights in @lessons-learned.md.
```

```plaintext
بازیابی
پیاده‌سازی فعلی را با @project-requirements.md مقایسه و انحرافات را شناسایی کنید. برنامه‌ای برای همسویی مجدد با الزامات اصلی ایجاد کرده، شکاف‌های بحرانی را اولویت‌بندی کنید. @scratchpad.md را با اقدامات اصلاحی و تنظیمات جدول زمانی به‌روز کنید. بینش‌های آموخته شده را در @lessons-learned.md مستند کنید.
```

---

## 7. Phase Transition | انتقال فاز

### 7.1 Phase Completion | تکمیل فاز

**When to use:** At the end of project phase.
**موارد استفاده:** در پایان فاز پروژه.
**Purpose:** Finalize phase and prepare for next.
**هدف:** نهایی‌سازی فاز و آماده‌سازی برای فاز بعدی.
**Example:** "Complete Phase 0 and prepare for Phase 1."
**مثال:** "تکمیل فاز صفر و آماده‌سازی برای فاز یک."

```plaintext
cycle
Evaluate completion status of current phase in @scratchpad.md. Verify all tasks are completed, tested, and documented. Create summary of achievements, challenges, and lessons learned. Archive phase documentation to /docs/phases and prepare @scratchpad.md for next phase.
```

```plaintext
چرخه
وضعیت تکمیل فاز فعلی را در @scratchpad.md ارزیابی کنید. تأیید کنید که تمام وظایف تکمیل، آزمایش و مستندسازی شده‌اند. خلاصه‌ای از دستاوردها، چالش‌ها و درس‌های آموخته شده ایجاد کنید. مستندات فاز را در /docs/phases بایگانی کرده و @scratchpad.md را برای فاز بعدی آماده کنید.
```

### 7.2 Release Preparation | آماده‌سازی انتشار

**When to use:** Before project release.
**موارد استفاده:** قبل از انتشار پروژه.
**Purpose:** Prepare for deployment.
**هدف:** آماده‌سازی برای استقرار.
**Example:** "Prepare v1.0.0 release."
**مثال:** "آماده‌سازی انتشار نسخه ۱.۰.۰."

```plaintext
cycle
Prepare [version] release by verifying all requirements are met, all tests pass, and documentation is complete. Update CHANGELOG.md, verify deployment scripts, create release checklist, and finalize version numbers. Document release process in @memories.md for future reference.
```

```plaintext
چرخه
انتشار [نسخه] را با تأیید برآورده شدن تمام نیازمندی‌ها، موفقیت تمام تست‌ها و تکمیل مستندات آماده کنید. CHANGELOG.md را به‌روز، اسکریپت‌های استقرار را تأیید، چک‌لیست انتشار ایجاد و شماره‌های نسخه را نهایی کنید. فرآیند انتشار را در @memories.md برای مراجعه آینده مستند کنید.
```

### 7.3 Retrospective | مرور و بازنگری

**When to use:** After phase completion.
**موارد استفاده:** پس از تکمیل فاز.
**Purpose:** Evaluate and learn.
**هدف:** ارزیابی و یادگیری.
**Example:** "Conduct retrospective for Phase 1."
**مثال:** "انجام مرور و بازنگری برای فاز یک."

```plaintext
cycle
Conduct retrospective analysis of [phase/milestone] comparing planned vs. actual outcomes. Identify successes, challenges, and areas for improvement. Document technical debt incurred, process improvements needed, and knowledge gained. Update @lessons-learned.md with key insights and @scratchpad.md with action items.
```

```plaintext
چرخه
تحلیل مرور و بازنگری [فاز/نقطه عطف] را با مقایسه نتایج برنامه‌ریزی شده و واقعی انجام دهید. موفقیت‌ها، چالش‌ها و زمینه‌های بهبود را شناسایی کنید. بدهی فنی ایجاد شده، بهبودهای فرآیند مورد نیاز و دانش کسب شده را مستند کنید. @lessons-learned.md را با بینش‌های کلیدی و @scratchpad.md را با موارد اقدام به‌روز کنید.
```

---

## 8. Task Analysis & Implementation | تحلیل و پیاده‌سازی تسک‌ها

### 8.1 Task Analysis | تحلیل تسک

**When to use:** Before starting complex task implementation.
**موارد استفاده:** قبل از شروع پیاده‌سازی تسک‌های پیچیده.
**Purpose:** Understand requirements and plan implementation.
**هدف:** درک نیازمندی‌ها و برنامه‌ریزی پیاده‌سازی.
**Example:** "Analyze database model creation task."
**مثال:** "تحلیل تسک ایجاد مدل‌های پایگاه داده."

```plaintext
plan
با استناد به @project-requirements.md، @scratchpad.md و @memories.md، لطفاً در مورد تسک [شناسه-تسک] [توضیح تسک] تحلیل جامعی ارائه دهید. نیازمندی‌های این تسک را بررسی کنید، محدوده کار را مشخص کنید، و مراحل اجرایی لازم برای تکمیل این تسک را در یک برنامه مرحله‌بندی شده ارائه دهید. بر روی [جنبه خاص] تمرکز کنید و درس‌های @lessons-learned.md را در طراحی در نظر بگیرید.
```

```plaintext
plan
Based on @project-requirements.md, @scratchpad.md, and @memories.md, please provide a comprehensive analysis of task [task-id] [task description]. Review the requirements for this task, define the scope of work, and present the implementation steps needed to complete this task in a structured plan. Focus on [specific aspect] and consider the lessons from @lessons-learned.md in your design.
```

### 8.2 Code Analysis | تحلیل کد

**When to use:** When analyzing existing codebase for changes.
**موارد استفاده:** هنگام تحلیل کدهای موجود برای تغییرات.
**Purpose:** Identify needed changes in existing code.
**هدف:** شناسایی تغییرات مورد نیاز در کد موجود.
**Example:** "Analyze database models for new requirements."
**مثال:** "تحلیل مدل‌های پایگاه داده برای نیازمندی‌های جدید."

```plaintext
plan
ریشه [مسئله/بخش کد] را با رویکرد سیستماتیک تحلیل کنید. کد فعلی، ساختار، و ارتباطات آن را بررسی کنید. برای درک بهتر نیازمندی‌های جدید و راه‌حل‌های ممکن، به @lessons-learned.md مراجعه کرده و راه‌حل‌های کوتاه‌مدت و بلندمدت را شناسایی کنید. لطفاً یک لیست مرحله‌بندی‌شده دقیق از تمام تغییرات مورد نیاز، اضافه‌ها و حذف‌های ضروری تهیه کنید. برای هر تغییر، دلیل فنی آن را توضیح دهید. یافته‌ها و طرح پیشنهادی را در @scratchpad.md به‌روز کنید.
```

```plaintext
plan
Analyze the root of [issue/code section] using a systematic approach. Review the current code, structure, and relationships. For better understanding of new requirements and possible solutions, refer to @lessons-learned.md and identify both short-term and long-term solutions. Please prepare a detailed, step-by-step list of all necessary changes, additions, and removals. For each change, explain the technical rationale. Update your findings and proposed plan in @scratchpad.md.
```

### 8.3 Step-by-Step Implementation | پیاده‌سازی گام به گام

**When to use:** When implementing complex tasks with multiple steps.
**موارد استفاده:** هنگام پیاده‌سازی تسک‌های پیچیده با مراحل متعدد.
**Purpose:** Execute implementation in structured phases.
**هدف:** اجرای پیاده‌سازی در مراحل ساختاریافته.
**Example:** "Implement database models one by one."
**مثال:** "پیاده‌سازی مدل‌های پایگاه داده به صورت گام به گام."

```plaintext
agent
لطفاً تسک [شناسه-تسک] [توضیح تسک] را طبق مشخصات @scratchpad.md و مطابق با @project-requirements.md پیاده‌سازی کنید. با [گام اول] شروع کنید و سپس به ترتیب، مراحل بعدی را انجام دهید. برای هر گام، [تمرکز خاص این گام] را پیاده‌سازی کرده و اطمینان حاصل کنید که کد از الگوهای موجود پیروی می‌کند، به خوبی مستند شده و شامل مدیریت خطای مناسب است. پس از هر گام، نتایج را بررسی و تأیید کنید. مستندات را طبق @documentations-inline-comments-changelog-docs.mdc به‌روز کنید.
```

```plaintext
agent
Please implement task [task-id] [task description] as specified in @scratchpad.md and in accordance with @project-requirements.md. Start with [first step] and then proceed through the subsequent steps in order. For each step, implement [specific focus of this step] and ensure that the code follows established patterns, is well-documented, and includes appropriate error handling. After each step, review and verify the results. Update documentation according to @documentations-inline-comments-changelog-docs.mdc.
```

---

Use these prompts in sequence for a structured development process. Each activates a specific AI mode to ensure comprehensive planning, implementation, documentation, and knowledge transfer. Customize prompts with specific project details when needed.

از این پرامپت‌ها به‌صورت ترتیبی برای فرآیند توسعه ساختاریافته استفاده کنید. هر کدام حالت خاصی از هوش مصنوعی را فعال می‌کند تا برنامه‌ریزی، پیاده‌سازی، مستندسازی و انتقال دانش جامع تضمین شود. در صورت نیاز، پرامپت‌ها را با جزئیات خاص پروژه سفارشی کنید.