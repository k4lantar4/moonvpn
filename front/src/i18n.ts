import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Initialize i18n with both Persian (fa) and English (en) translations
i18n
  .use(initReactI18next)
  .init({
    resources: {
      fa: {
        translation: {
          // Auth pages
          'ورود به حساب کاربری': 'ورود به حساب کاربری',
          'خوش آمدید! لطفاً اطلاعات خود را وارد کنید': 'خوش آمدید! لطفاً اطلاعات خود را وارد کنید',
          'ایمیل': 'ایمیل',
          'رمز عبور': 'رمز عبور',
          'مرا به خاطر بسپار': 'مرا به خاطر بسپار',
          'فراموشی رمز عبور': 'فراموشی رمز عبور',
          'ورود': 'ورود',
          'در حال ورود...': 'در حال ورود...',
          'یا': 'یا',
          'گوگل': 'گوگل',
          'گیت‌هاب': 'گیت‌هاب',
          'حساب کاربری ندارید؟': 'حساب کاربری ندارید؟',
          'ثبت نام': 'ثبت نام',
          'لطفاً ایمیل و رمز عبور را وارد کنید': 'لطفاً ایمیل و رمز عبور را وارد کنید',
          'ایمیل یا رمز عبور اشتباه است': 'ایمیل یا رمز عبور اشتباه است',
          
          // Register page
          'ایجاد حساب کاربری': 'ایجاد حساب کاربری',
          'ثبت نام در چند مرحله ساده': 'ثبت نام در چند مرحله ساده',
          'اطلاعات حساب': 'اطلاعات حساب',
          'اطلاعات شخصی': 'اطلاعات شخصی',
          'تأیید': 'تأیید',
          'تکرار رمز عبور': 'تکرار رمز عبور',
          'رمز عبور باید حداقل ۸ کاراکتر باشد': 'رمز عبور باید حداقل ۸ کاراکتر باشد',
          'تکرار رمز عبور مطابقت ندارد': 'تکرار رمز عبور مطابقت ندارد',
          'قبلی': 'قبلی',
          'بعدی': 'بعدی',
          'ثبت نام و ایجاد حساب': 'ثبت نام و ایجاد حساب',
          'در حال ثبت نام...': 'در حال ثبت نام...',
          'قبلاً حساب کاربری دارید؟': 'قبلاً حساب کاربری دارید؟',
          'نام و نام خانوادگی': 'نام و نام خانوادگی',
          'شماره موبایل': 'شماره موبایل',
          'موافقت با': 'موافقت با',
          'شرایط و قوانین': 'شرایط و قوانین',
          'سرویس': 'سرویس',
          'لطفاً نام و نام خانوادگی خود را وارد کنید': 'لطفاً نام و نام خانوادگی خود را وارد کنید',
          'لطفاً شماره موبایل خود را وارد کنید': 'لطفاً شماره موبایل خود را وارد کنید',
          'لطفاً شرایط و قوانین را بپذیرید': 'لطفاً شرایط و قوانین را بپذیرید',
          'کد تأیید به شماره موبایل شما ارسال شد': 'کد تأیید به شماره موبایل شما ارسال شد',
          'کد تأیید را وارد کنید': 'کد تأیید را وارد کنید',
          'کد تأیید': 'کد تأیید',
          'ارسال مجدد کد': 'ارسال مجدد کد',
          'تأیید کد': 'تأیید کد',
          'کد را دریافت نکردید؟': 'کد را دریافت نکردید؟',
          'ارسال مجدد': 'ارسال مجدد',
          'ثبت نام با موفقیت انجام شد!': 'ثبت نام با موفقیت انجام شد!',
          'حساب کاربری شما با موفقیت ایجاد شد.': 'حساب کاربری شما با موفقیت ایجاد شد.',
          'ورود به داشبورد': 'ورود به داشبورد',
          
          // Forgot password page
          'بازیابی رمز عبور': 'بازیابی رمز عبور',
          'در چند مرحله ساده رمز عبور خود را بازیابی کنید': 'در چند مرحله ساده رمز عبور خود را بازیابی کنید',
          'درخواست بازیابی': 'درخواست بازیابی',
          'تأیید کد': 'تأیید کد',
          'رمز عبور جدید': 'رمز عبور جدید',
          'درخواست بازیابی رمز عبور': 'درخواست بازیابی رمز عبور',
          'ایمیل خود را وارد کنید تا کد بازیابی برای شما ارسال شود.': 'ایمیل خود را وارد کنید تا کد بازیابی برای شما ارسال شود.',
          'لطفاً ایمیل خود را وارد کنید': 'لطفاً ایمیل خود را وارد کنید',
          'فرمت ایمیل نامعتبر است': 'فرمت ایمیل نامعتبر است',
          'خطا در ارسال درخواست. لطفاً دوباره تلاش کنید': 'خطا در ارسال درخواست. لطفاً دوباره تلاش کنید',
          'کد ارسال شده به ایمیل زیر را وارد کنید:': 'کد ارسال شده به ایمیل زیر را وارد کنید:',
          'لطفاً کد تأیید را وارد کنید': 'لطفاً کد تأیید را وارد کنید',
          'کد تأیید باید ۶ رقم باشد': 'کد تأیید باید ۶ رقم باشد',
          'کد تأیید نامعتبر است': 'کد تأیید نامعتبر است',
          'خطا در تأیید کد. لطفاً دوباره تلاش کنید': 'خطا در تأیید کد. لطفاً دوباره تلاش کنید',
          'تعیین رمز عبور جدید': 'تعیین رمز عبور جدید',
          'رمز عبور جدید را وارد کنید.': 'رمز عبور جدید را وارد کنید.',
          'رمز عبور جدید': 'رمز عبور جدید',
          'تکرار رمز عبور جدید': 'تکرار رمز عبور جدید',
          'لطفاً رمز عبور جدید را وارد کنید': 'لطفاً رمز عبور جدید را وارد کنید',
          'خطا در بازنشانی رمز عبور. لطفاً دوباره تلاش کنید': 'خطا در بازنشانی رمز عبور. لطفاً دوباره تلاش کنید',
          'بازگشت': 'بازگشت',
          'ارسال کد': 'ارسال کد',
          'بازنشانی رمز عبور': 'بازنشانی رمز عبور',
          'لطفاً صبر کنید...': 'لطفاً صبر کنید...',
          'رمز عبور خود را به یاد آوردید؟': 'رمز عبور خود را به یاد آوردید؟',
          'بازنشانی موفق': 'بازنشانی موفق',
          'رمز عبور با موفقیت بازنشانی شد': 'رمز عبور با موفقیت بازنشانی شد',
          'اکنون می‌توانید با رمز عبور جدید وارد حساب کاربری خود شوید.': 'اکنون می‌توانید با رمز عبور جدید وارد حساب کاربری خود شوید.',
          'ورود به حساب': 'ورود به حساب',
          
          // Layout
          'تغییر زبان': 'تغییر زبان',
          'تغییر تم': 'تغییر تم',
          'تمامی حقوق محفوظ است': 'تمامی حقوق محفوظ است',
          'شرایط استفاده': 'شرایط استفاده',
          'حریم خصوصی': 'حریم خصوصی',
          'پشتیبانی': 'پشتیبانی',

          // Loading
          'در حال بارگذاری...': 'در حال بارگذاری...',
          
          // Authorization
          'دسترسی محدود شده': 'دسترسی محدود شده',
          'شما اجازه دسترسی به این صفحه را ندارید': 'شما اجازه دسترسی به این صفحه را ندارید',
          'بازگشت به صفحه اصلی': 'بازگشت به صفحه اصلی',
          'خطا در بارگذاری اطلاعات کاربری': 'خطا در بارگذاری اطلاعات کاربری',
          'خطا در ورود به سیستم': 'خطا در ورود به سیستم',
          'خطا در ثبت نام': 'خطا در ثبت نام',
          'خطا در ارسال درخواست بازیابی رمز عبور': 'خطا در ارسال درخواست بازیابی رمز عبور',
          'خطا در بازنشانی رمز عبور': 'خطا در بازنشانی رمز عبور',
          'خطا در تأیید کد': 'خطا در تأیید کد',
          
          // User roles
          'کاربر': 'کاربر',
          'فروشنده': 'فروشنده',
          'مدیر': 'مدیر',
          'نقش کاربری': 'نقش کاربری',
          'مدیریت نقش‌ها': 'مدیریت نقش‌ها',
          'تغییر نقش': 'تغییر نقش',

          // Auth pages
          auth: {
            login: 'ورود',
            register: 'ثبت نام',
            forgotPassword: 'فراموشی رمز عبور',
            resetPassword: 'بازنشانی رمز عبور',
            loginToAccount: 'ورود به حساب کاربری',
            createAccount: 'ایجاد حساب کاربری',
            emailAddress: 'آدرس ایمیل',
            password: 'رمز عبور',
            confirmPassword: 'تکرار رمز عبور',
            rememberMe: 'مرا به خاطر بسپار',
            dontHaveAccount: 'حساب کاربری ندارید؟',
            alreadyHaveAccount: 'قبلاً ثبت نام کرده‌اید؟',
            forgotYourPassword: 'رمز عبور خود را فراموش کرده‌اید؟',
            recoverPassword: 'بازیابی رمز عبور',
            enterEmail: 'ایمیل خود را وارد کنید',
            enterVerificationCode: 'کد تایید را وارد کنید',
            enterNewPassword: 'رمز عبور جدید را وارد کنید',
            backToLogin: 'بازگشت به صفحه ورود',
            verificationCode: 'کد تایید',
            newPassword: 'رمز عبور جدید',
            invalidEmail: 'آدرس ایمیل معتبر نیست',
            invalidPassword: 'رمز عبور باید حداقل ۸ کاراکتر باشد',
            passwordMismatch: 'رمز عبور و تکرار آن مطابقت ندارند',
            invalidCode: 'کد وارد شده معتبر نیست',
            sendCode: 'ارسال کد',
            verify: 'تایید',
            reset: 'بازنشانی',
            continue: 'ادامه',
            submit: 'ارسال',
          },
          
          // Registration pages
          register: {
            step1Title: 'اطلاعات حساب کاربری',
            step2Title: 'اطلاعات شخصی',
            step3Title: 'تایید حساب کاربری',
            fullName: 'نام و نام خانوادگی',
            phoneNumber: 'شماره تلفن همراه',
            agreeToTerms: 'قوانین و مقررات سایت را می‌پذیرم',
            successMessage: 'ثبت نام با موفقیت انجام شد!',
            successDescription: 'اکنون می‌توانید وارد حساب کاربری خود شوید.',
            next: 'مرحله بعد',
            previous: 'مرحله قبل',
            finish: 'پایان',
            enterFullName: 'نام و نام خانوادگی خود را وارد کنید',
            enterPhoneNumber: 'شماره تلفن همراه خود را وارد کنید',
            mustAgreeToTerms: 'برای ادامه باید قوانین و مقررات سایت را بپذیرید',
            invalidPhoneNumber: 'شماره تلفن همراه معتبر نیست',
            codeHasBeenSent: 'کد تایید به شماره همراه شما ارسال شد',
            didntReceiveCode: 'کدی دریافت نکردید؟',
            resendCode: 'ارسال مجدد',
          },
          
          // Password recovery
          passwordRecovery: {
            step1Title: 'درخواست بازیابی رمز عبور',
            step2Title: 'تایید کد ارسال شده',
            step3Title: 'تعیین رمز عبور جدید',
            step4Title: 'تکمیل بازیابی',
            successMessage: 'رمز عبور با موفقیت تغییر کرد!',
            successDescription: 'اکنون می‌توانید با رمز عبور جدید وارد شوید.',
            instructions: 'ایمیل یا شماره همراه خود را وارد کنید تا کد تایید برای شما ارسال شود.',
            codeInstructions: 'کد تایید ارسال شده به ایمیل یا شماره همراه خود را وارد کنید.',
            passwordInstructions: 'رمز عبور جدید خود را وارد کنید.',
          },
          
          // Layout
          layout: {
            appName: 'مدیریت وی‌پی‌ان',
            appTagline: 'سامانه مدیریت خدمات وی‌پی‌ان',
            toggleTheme: 'تغییر تم',
            toggleLanguage: 'تغییر زبان',
            copyright: '© {{year}} تمامی حقوق محفوظ است.',
          },
          
          // Loading
          loading: {
            message: 'در حال بارگذاری...',
          },
          
          // Authorization
          authorization: {
            accessRestricted: 'دسترسی محدود شده',
            noPermission: 'شما اجازه دسترسی به این صفحه را ندارید',
            backToHome: 'بازگشت به صفحه اصلی',
          },
          
          // User roles
          roles: {
            user: 'کاربر',
            reseller: 'نمایندگی',
            admin: 'مدیر سیستم',
          },
          
          // Dashboard
          dashboard: {
            title: 'پنل کاربری',
            welcomeMessage: 'به پنل کاربری خوش آمدید',
            welcomeUser: 'خوش آمدید، {{name}}',
            introText: 'از این قسمت می‌توانید خدمات وی‌پی‌ان خود را مدیریت کنید، اشتراک خریداری کنید و وضعیت سرویس‌های خود را مشاهده نمایید.',
            overview: 'خلاصه وضعیت',
            vpnServices: 'سرویس‌های وی‌پی‌ان',
            billing: 'صورتحساب‌ها',
            payment: 'پرداخت',
            settings: 'تنظیمات',
            profile: 'پروفایل',
            logout: 'خروج',
            
            // Subscription status
            subscriptionStatus: 'وضعیت اشتراک',
            active: 'فعال',
            expired: 'منقضی شده',
            pending: 'در انتظار',
            expiresOn: 'تاریخ انقضا',
            daysLeft: 'روز باقی‌مانده',
            daysRemaining: 'روز باقی‌مانده',
            
            // Data usage
            dataUsage: 'مصرف حجم',
            totalUsage: 'کل مصرف',
            
            // Server status
            serverStatus: 'وضعیت سرورها',
            serverName: 'نام سرور',
            status: 'وضعیت',
            latency: 'تاخیر',
            online: 'آنلاین',
            offline: 'آفلاین',
            maintenance: 'در حال تعمیر',
            
            // Stats
            totalConnections: 'تعداد اتصالات',
            availableServers: 'سرورهای فعال',
            
            // Activities
            recentActivities: 'فعالیت‌های اخیر',
            
            // User
            user: 'کاربر',
          },
          
          // Payment
          payment: {
            walletBalance: 'موجودی کیف پول',
            lastDeposit: 'آخرین شارژ',
            pendingTransactions: 'تراکنش‌های در انتظار',
            walletTopup: 'شارژ کیف پول',
            cardPayment: 'پرداخت با کارت',
            zarinpalPayment: 'پرداخت از طریق زرین‌پال',
            paymentHistory: 'تاریخچه پرداخت‌ها',
            chooseAmount: 'مبلغ را انتخاب کنید',
            customAmount: 'مبلغ دلخواه',
            toman: 'تومان',
            choosePaymentMethod: 'روش پرداخت را انتخاب کنید',
            cardNumber: 'شماره کارت',
            accountOwner: 'به نام',
            bank: 'بانک',
            cardToCard: 'کارت به کارت',
            uploadReceipt: 'آپلود رسید پرداخت',
            paymentDate: 'تاریخ پرداخت',
            trackingCode: 'کد پیگیری',
            description: 'توضیحات',
            proceed: 'ادامه',
            cancel: 'انصراف',
          },
          
          // Admin Dashboard
          admin: {
            dashboard: 'داشبورد مدیریت',
            userManagement: 'مدیریت کاربران',
            serverManagement: 'مدیریت سرورها',
            plans: 'مدیریت اشتراک‌ها',
            financialReports: 'گزارش‌های مالی',
            systemSettings: 'تنظیمات سیستم',
            roleManagement: 'مدیریت نقش‌ها',
            
            // User management
            totalUsers: 'تعداد کل کاربران',
            activeUsers: 'کاربران فعال',
            newUsers: 'کاربران جدید',
            userList: 'لیست کاربران',
            searchUsers: 'جستجوی کاربران',
            addUser: 'افزودن کاربر',
            editUser: 'ویرایش کاربر',
            deleteUser: 'حذف کاربر',
            lastLogin: 'آخرین ورود',
            userDetails: 'جزئیات کاربر',
            
            // Role management
            roles: 'نقش‌ها',
            changeRole: 'تغییر نقش',
            confirmRoleChange: 'آیا از تغییر نقش این کاربر اطمینان دارید؟',
            roleChanged: 'نقش کاربر با موفقیت تغییر کرد',
            confirmDelete: 'آیا از حذف این کاربر اطمینان دارید؟',
            userDeleted: 'کاربر با موفقیت حذف شد',
            userAdded: 'کاربر با موفقیت اضافه شد',
            userUpdated: 'اطلاعات کاربر با موفقیت به‌روز شد',
            
            // Server management
            addServer: 'افزودن سرور',
            editServer: 'ویرایش سرور',
            deleteServer: 'حذف سرور',
            serverIP: 'آدرس IP',
            serverLocation: 'موقعیت سرور',
            serverCapacity: 'ظرفیت',
            currentLoad: 'بار فعلی',
            
            // Subscription plans
            addPlan: 'افزودن اشتراک',
            editPlan: 'ویرایش اشتراک',
            deletePlan: 'حذف اشتراک',
            planName: 'نام اشتراک',
            planDuration: 'مدت زمان',
            planPrice: 'قیمت',
            dataLimit: 'محدودیت حجم',
            features: 'ویژگی‌ها',
            
            // Financial reports
            totalRevenue: 'درآمد کل',
            monthlyRevenue: 'درآمد ماهانه',
            transactions: 'تراکنش‌ها',
            dateRange: 'بازه زمانی',
            
            // System settings
            generalSettings: 'تنظیمات عمومی',
            notificationSettings: 'تنظیمات اعلان‌ها',
            backupSettings: 'تنظیمات پشتیبان‌گیری',
            saveSettings: 'ذخیره تنظیمات',
            settingsSaved: 'تنظیمات با موفقیت ذخیره شدند',
          },
        }
      },
      en: {
        translation: {
          // Auth pages
          'ورود به حساب کاربری': 'Login to Your Account',
          'خوش آمدید! لطفاً اطلاعات خود را وارد کنید': 'Welcome! Please enter your details',
          'ایمیل': 'Email',
          'رمز عبور': 'Password',
          'مرا به خاطر بسپار': 'Remember me',
          'فراموشی رمز عبور': 'Forgot Password',
          'ورود': 'Login',
          'در حال ورود...': 'Logging in...',
          'یا': 'or',
          'گوگل': 'Google',
          'گیت‌هاب': 'GitHub',
          'حساب کاربری ندارید؟': 'Don\'t have an account?',
          'ثبت نام': 'Register',
          'لطفاً ایمیل و رمز عبور را وارد کنید': 'Please enter your email and password',
          'ایمیل یا رمز عبور اشتباه است': 'Email or password is incorrect',
          
          // Register page
          'ایجاد حساب کاربری': 'Create Account',
          'ثبت نام در چند مرحله ساده': 'Register in a few simple steps',
          'اطلاعات حساب': 'Account Info',
          'اطلاعات شخصی': 'Personal Info',
          'تأیید': 'Verification',
          'تکرار رمز عبور': 'Confirm Password',
          'رمز عبور باید حداقل ۸ کاراکتر باشد': 'Password must be at least 8 characters',
          'تکرار رمز عبور مطابقت ندارد': 'Passwords do not match',
          'قبلی': 'Previous',
          'بعدی': 'Next',
          'ثبت نام و ایجاد حساب': 'Register and Create Account',
          'در حال ثبت نام...': 'Registering...',
          'قبلاً حساب کاربری دارید؟': 'Already have an account?',
          'نام و نام خانوادگی': 'Full Name',
          'شماره موبایل': 'Mobile Number',
          'موافقت با': 'I agree to the',
          'شرایط و قوانین': 'Terms and Conditions',
          'سرویس': 'of service',
          'لطفاً نام و نام خانوادگی خود را وارد کنید': 'Please enter your full name',
          'لطفاً شماره موبایل خود را وارد کنید': 'Please enter your mobile number',
          'لطفاً شرایط و قوانین را بپذیرید': 'Please accept the terms and conditions',
          'کد تأیید به شماره موبایل شما ارسال شد': 'Verification code sent to your mobile number',
          'کد تأیید را وارد کنید': 'Enter verification code',
          'کد تأیید': 'Verification Code',
          'ارسال مجدد کد': 'Resend Code',
          'تأیید کد': 'Verify Code',
          'کد را دریافت نکردید؟': 'Didn\'t receive the code?',
          'ارسال مجدد': 'Resend',
          'ثبت نام با موفقیت انجام شد!': 'Registration Successful!',
          'حساب کاربری شما با موفقیت ایجاد شد.': 'Your account has been created successfully.',
          'ورود به داشبورد': 'Go to Dashboard',
          
          // Forgot password page
          'بازیابی رمز عبور': 'Password Recovery',
          'در چند مرحله ساده رمز عبور خود را بازیابی کنید': 'Recover your password in a few simple steps',
          'درخواست بازیابی': 'Request Recovery',
          'تأیید کد': 'Verify Code',
          'رمز عبور جدید': 'New Password',
          'درخواست بازیابی رمز عبور': 'Password Recovery Request',
          'ایمیل خود را وارد کنید تا کد بازیابی برای شما ارسال شود.': 'Enter your email to receive a recovery code.',
          'لطفاً ایمیل خود را وارد کنید': 'Please enter your email',
          'فرمت ایمیل نامعتبر است': 'Invalid email format',
          'خطا در ارسال درخواست. لطفاً دوباره تلاش کنید': 'Error sending request. Please try again',
          'کد ارسال شده به ایمیل زیر را وارد کنید:': 'Enter the code sent to the email below:',
          'لطفاً کد تأیید را وارد کنید': 'Please enter the verification code',
          'کد تأیید باید ۶ رقم باشد': 'Verification code must be 6 digits',
          'کد تأیید نامعتبر است': 'Invalid verification code',
          'خطا در تأیید کد. لطفاً دوباره تلاش کنید': 'Error verifying code. Please try again',
          'تعیین رمز عبور جدید': 'Set New Password',
          'رمز عبور جدید را وارد کنید.': 'Enter your new password.',
          'رمز عبور جدید': 'New Password',
          'تکرار رمز عبور جدید': 'Confirm New Password',
          'لطفاً رمز عبور جدید را وارد کنید': 'Please enter your new password',
          'خطا در بازنشانی رمز عبور. لطفاً دوباره تلاش کنید': 'Error resetting password. Please try again',
          'بازگشت': 'Back',
          'ارسال کد': 'Send Code',
          'بازنشانی رمز عبور': 'Reset Password',
          'لطفاً صبر کنید...': 'Please wait...',
          'رمز عبور خود را به یاد آوردید؟': 'Remembered your password?',
          'بازنشانی موفق': 'Reset Successful',
          'رمز عبور با موفقیت بازنشانی شد': 'Password successfully reset',
          'اکنون می‌توانید با رمز عبور جدید وارد حساب کاربری خود شوید.': 'You can now log in with your new password.',
          'ورود به حساب': 'Login to Account',
          
          // Layout
          'تغییر زبان': 'Change Language',
          'تغییر تم': 'Toggle Theme',
          'تمامی حقوق محفوظ است': 'All Rights Reserved',
          'شرایط استفاده': 'Terms of Use',
          'حریم خصوصی': 'Privacy Policy',
          'پشتیبانی': 'Support',

          // Loading
          'در حال بارگذاری...': 'Loading...',
          
          // Authorization
          'دسترسی محدود شده': 'Access Restricted',
          'شما اجازه دسترسی به این صفحه را ندارید': 'You do not have permission to access this page',
          'بازگشت به صفحه اصلی': 'Return to Home',
          'خطا در بارگذاری اطلاعات کاربری': 'Error loading user information',
          'خطا در ورود به سیستم': 'Error logging in',
          'خطا در ثبت نام': 'Error registering',
          'خطا در ارسال درخواست بازیابی رمز عبور': 'Error sending password recovery request',
          'خطا در بازنشانی رمز عبور': 'Error resetting password',
          'خطا در تأیید کد': 'Error verifying code',
          
          // User roles
          'کاربر': 'User',
          'فروشنده': 'Reseller',
          'مدیر': 'Admin',
          'نقش کاربری': 'User Role',
          'مدیریت نقش‌ها': 'Role Management',
          'تغییر نقش': 'Change Role',
        },
      }
    },
    lng: 'fa', // Default language is Persian
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false, // React already does escaping
    },
  });

// Set the initial direction based on default language
document.dir = 'rtl';

export default i18n; 