# 🌙 MoonVPN AI Prompts - AI Commands Guide | راهنمای دستورات هوش مصنوعی

This file (@PROMPT.md) contains a complete set of structured prompts for guiding the AI through the different stages of the MoonVPN project's development. Follow these prompts for Plan Mode, Agent Mode, Documentation updates, and Knowledge Management. Each prompt includes references to key files such as @scratchpad.md, @memories, @project-requirements.md, @lessons-learned, and @documentations-inline-comments-changelog-docs.

این فایل (@PROMPT.md) شامل مجموعه‌ای جامع از پرامپت‌های ساختاریافته برای هدایت هوش مصنوعی در مراحل مختلف توسعه پروژه MoonVPN است. از این پرامپت‌ها برای حالت برنامه‌ریزی، اجرای تغییرات (Agent Mode)، به‌روزرسانی مستندات و مدیریت دانش استفاده کنید. هر پرامپت شامل ارجاعات به فایل‌های کلیدی مانند @scratchpad.md، @memories، @project-requirements.md، @lessons-learned و @documentations-inline-comments-changelog-docs می‌باشد.

---

## 1. Plan Mode | حالت برنامه‌ریزی

### 1.1 System Planning Initialization | شروع برنامه‌ریزی سیستمی

```plaintext
plan
Considering @scratchpad.md, @memories, and @project-requirements.md, please develop a comprehensive plan for the target task [specify task]. Include requirements, key questions, execution steps, and system-wide impact.
```

```plaintext
پلن
با توجه به @scratchpad.md، @memories و @project-requirements.md، لطفاً یک برنامه جامع برای [تسک/هدف] تهیه کنید. نیازمندی‌ها، سوالات کلیدی، گام‌های اجرایی و تأثیر کلی بر روی سیستم را شرح دهید.
```

### 1.2 Architecture and Dependency Analysis | تحلیل معماری و وابستگی‌ها

```plaintext
plan
Please provide a detailed analysis of how the proposed [change/new feature] will impact the current system architecture and dependencies. Refer to @lessons-learned for past insights and @memories for similar experiences.
```

```plaintext
پلن
لطفاً تحلیل دقیقی از تأثیر [تغییر/ویژگی جدید] بر معماری فعلی سیستم و وابستگی‌ها ارائه دهید. به @lessons-learned برای درس‌های گذشته و به @memories برای تجربیات مشابه مراجعه کنید.
```

### 1.3 Feasibility and Risk Assessment | بررسی امکان‌پذیری و ریسک

```plaintext
plan
Assess whether the proposed [feature/change] is feasible considering the current system architecture and @project-requirements.md. Evaluate risks, challenges, and potential impacts on security, performance, and scalability.
```

```plaintext
پلن
ارزیابی کنید که آیا [ویژگی/تغییر] پیشنهادی با توجه به معماری فعلی سیستم و @project-requirements.md قابل اجراست یا خیر. ریسک‌ها، چالش‌ها و تأثیرات احتمالی بر امنیت، عملکرد و مقیاس‌پذیری را بررسی نمایید.
```

### 1.4 Root Cause (Chain) Analysis | تحلیل زنجیره‌ای مشکلات

```plaintext
plan
A problem has been identified: [describe problem] in [system section]. Utilize chain-of-thought analysis and insights from @lessons-learned to identify the root cause and propose systemic solutions.
```

```plaintext
پلن
مشکلی شناسایی شده است: [توصیف مشکل] در [بخش سیستم]. از تحلیل زنجیره‌ای فکر و درس‌های @lessons-learned استفاده کنید تا ریشه مشکل را شناسایی و راهکارهای سیستمی ارائه دهید.
```

---

## 2. Agent Mode | حالت اجرا

### 2.1 Implementing Change with Integrity | پیاده‌سازی با حفظ یکپارچگی

```plaintext
agent
Based on the plan outlined in @scratchpad.md and following @project-requirements.md, implement the [change/feature] while maintaining system integrity. Ensure all documentation and testing standards are met.
```

```plaintext
اژن
بر اساس برنامه تعیین شده در @scratchpad.md و مطابق با @project-requirements.md، لطفاً [تغییر/ویژگی] را با حفظ یکپارچگی سیستم پیاده‌سازی کنید و از رعایت استانداردهای مستندسازی و تست اطمینان حاصل نمایید.
```

### 2.2 Optimization and Enhancement | بهینه‌سازی و بهبود

```plaintext
agent
Please optimize [section/feature] with the goal of enhancing [performance/security/scalability]. Leverage insights from @lessons-learned to prevent recurring issues.
```

```plaintext
اژن
لطفاً [بخش/ویژگی] را با هدف بهبود [عملکرد/امنیت/مقیاس‌پذیری] بهینه‌سازی کنید. از درس‌های @lessons-learned برای جلوگیری از بروز مشکلات مشابه استفاده نمایید.
```

### 2.3 Documentation Update | به‌روزرسانی مستندات

```plaintext
agent
Following the latest changes, update the necessary documentation in @documentations-inline-comments-changelog-docs. Ensure that all inline comments, API documentation, and changelog entries are current.
```

```plaintext
اژن
با توجه به تغییرات اخیر، لطفاً مستندات لازم را در @documentations-inline-comments-changelog-docs به‌روز کنید. اطمینان حاصل کنید که تمامی کامنت‌های داخل خط، مستندات API، و ورودی‌های تاریخچه تغییرات به‌روز باشند.
```

---

## 3. Knowledge Management | مدیریت دانش

### 3.1 Updating Memories and Lessons Learned | به‌روزرسانی @memories و @lessons-learned

```plaintext
knowledge
Review and update @memories and @lessons-learned with insights from the current development cycle. Document key technical decisions, challenges, and resolutions.
```

```plaintext
دانش
لطفاً @memories و @lessons-learned را با درس‌ها و نکات به‌دست آمده از چرخه فعلی توسعه به‌روز کنید. تصمیمات فنی کلیدی، چالش‌ها و راه‌حل‌های ارائه شده را مستند نمایید.
```

---

## 4. Cycle Completion | پایان چرخه

### 4.1 Conversation Summary and Memory Update | خلاصه مکالمه و به‌روزرسانی @memories

```plaintext
cycle
Summarize the key outcomes of this conversation, and update @memories with action items and decisions taken.
```

```plaintext
چرخه
خلاصه‌ای از نتایج کلیدی این مکالمه ارائه دهید و @memories را با موارد اقدام و تصمیمات اتخاذ شده به‌روز نمایید.
```

---

Remember: Always use these prompts in sequence to ensure a clear, traceable, and efficient development process. Each prompt is designed to trigger a specific mode in the AI, ensuring thorough planning, execution, and documentation.

به یاد داشته باشید: همیشه از این پرامپت‌ها به صورت ترتیبی استفاده کنید تا فرآیند توسعه به صورت شفاف، قابل پیگیری و کارآمد باشد. هر پرامپت به گونه‌ای طراحی شده است که یک حالت خاص را در هوش مصنوعی فعال کند و برنامه‌ریزی، اجرا، و مستندسازی به طور کامل انجام شود. 