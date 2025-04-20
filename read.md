{
	"folders": [
		{
			"path": "moonvpn"
		}
	],
	"settings": {
		"terminal.integrated.profiles.linux": {
			"bash": {
				"path": "bash",
				"args": [
					"--login"
				],
				"icon": "terminal-bash"
			}
		},
		"terminal.integrated.defaultProfile.linux": "bash",
		"terminal.integrated.shellIntegration.enabled": true,
		"terminal.integrated.commandsToSkipShell": [
			"exit",
			"quit"
		],
		"terminal.integrated.cwd": "/root/moonvpn",
		"terminal.integrated.inheritEnv": true,
		"terminal.integrated.allowChords": true,
		"terminal.integrated.confirmOnExit": "never",
		"terminal.integrated.autoReplies": {
			"Do you want to exit the Python shell?": "yes",
			"Do you really want to exit [y/N]": "y",
			"Press any key to continue...": "\r",
			"Type 'exit' to exit": "exit",
			"--More--": "q",
			"[Y/n]": "Y",
			"(y/N)": "y",
			"Continue? [y/N]": "y",
			"Are you sure? [y/N]": "y",
			"Terminate batch job (Y/N)?": "Y",
			"Do you want to terminate the batch job (Y/N)?": "Y",
			"Press Enter to continue...": "\r",
			"Press ENTER to continue": "\r",
			"Press any key to continue . . .": "\r",
			"Would you like to continue [Y/n]?": "Y",
			"Press Ctrl+C to abort": "\u0003",
			"Press RETURN to continue, or q to quit": "\r",
			"Do you wish to continue [y/N]?": "y"
		},
		"terminal.integrated.defaultLocation": "view",
		"terminal.integrated.autoExitBehavior": "never",
		"terminal.integrated.exitBehavior": "always",
		"terminal.integrated.env.linux": {
			"TERM": "xterm-256color"
		},
		"terminal.integrated.gpuAcceleration": "on",
		"terminal.integrated.scrollback": 100,
		"terminal.integrated.enablePersistentSessions": true,
		"terminal.integrated.persistentSessionReviveProcess": "onExit",
		"terminal.integrated.shellArgs.linux": [
			"--login"
		],
		"terminal.integrated.copyOnSelection": true,
		"terminal.integrated.cursorBlinking": true,
		"terminal.integrated.cursorStyle": "line",
		"terminal.integrated.rightClickBehavior": "default",
		"terminal.integrated.sendKeybindingsToShell": true,
		"terminal.integrated.tabs.enabled": true,
		"terminal.integrated.tabs.location": "right",
		"terminal.integrated.detectLocale": "on",
		"terminal.integrated.macOptionIsMeta": true,
		"terminal.integrated.showExitAlert": false,
		"terminal.integrated.fastScrollSensitivity": 5,
		"terminal.integrated.mouseWheelScrollSensitivity": 1.5,
		"terminal.integrated.enableFileLinks": true,
		"terminal.integrated.rendererType": "auto",
		"terminal.integrated.shellIntegration.decorationsEnabled": "both",
		"terminal.integrated.smoothScrolling": true,
		"terminal.integrated.ignoreBracketedPasteMode": false,
		"terminal.integrated.localEchoLatencyThreshold": 0,
		"terminal.integrated.localEchoEnabled": true,
		"terminal.integrated.localEchoStyle": "dim",
		"terminal.integrated.defaultProfile.osx": "bash",
		"terminal.integrated.defaultProfile.windows": "Command Prompt",
		"terminal.integrated.limitCharacters": 2000,
		"terminal.integrated.shellIntegration.history": 50,
		// 🌙 ظاهر و نمایش
		"workbench.colorTheme": "Default Dark+",
		"workbench.startupEditor": "none",
		"window.density.editorTabHeight": "default",
		// ⚙️ ادیتور
		"editor.suggestSelection": "first",
		"editor.tabSize": 4,
		"editor.insertSpaces": true,
		"editor.formatOnSave": true,
		// 🌐 فارسی و فونت
		"editor.rtlDetect": true,
		"editor.renderControlCharacters": true,
		"editor.fontFamily": "Vazirmatn, Fira Code, Consolas, 'Courier New', monospace",
		"editor.fontLigatures": false,
		"terminal.integrated.fontFamily": "monospace",
		// 📄 پیش‌نمایش‌ها و مارک‌داون
		"markdown.preview.fontFamily": "Vazirmatn, sans-serif",
		"markdown.preview.lineHeight": 1.8,
		"markdown.preview.scrollPreviewWithEditor": true,
		"markdown.preview.scrollEditorWithPreview": true,
		"markdown.preview.markEditorSelection": true,
		// 🪄 رفع نهایی مشکلات BiDi
		"editor.unicodeHighlight.allowedCharacters": {
			"\u200c": true, // ZWNJ
			"\u200e": true, // LRM
			"\u200f": true // RLM
		},
		"editor.unicodeHighlight.invisibleCharacters": false,
		// تنظیمات اضافی برای بهبود عملکرد ترمینال در SSH
		"remote.SSH.useLocalServer": false,
		"remote.SSH.showLoginTerminal": true,
		"remote.SSH.remotePlatform": "linux",
		"remote.SSH.connectTimeout": 60,
		"remote.SSH.defaultExtensions": [
			"ms-vscode.remote-explorer"
		],
		"remote.SSH.enableDynamicForwarding": true,
		"remote.SSH.enableRemoteCommand": true,
		"remote.SSH.localServerDownload": "auto",
		"remote.SSH.lockfilesInTmp": true,
		"remote.SSH.logLevel": "debug",
		"remote.SSH.ignoreDefaultExtensions": [
			"github.vscode-pull-request-github"
		],
		"remote.SSH.path": "ssh",
		"remote.SSH.serverPickPortsFromRange": {
			"min": 50000,
			"max": 55000
		},
		"remote.SSH.serverInstallPath": "~/.vscode-server",
		"remote.SSH.maxReconnectionAttempts": 5,
		"remote.SSH.suppressWindowsSshWarning": true,
		// تنظیمات مخصوص ترمینال برای استفاده در SSH
		"terminal.integrated.allowChords": false,
		"terminal.integrated.windowsEnableConpty": true,
		"terminal.integrated.automationShell.linux": "bash",
		"terminal.integrated.inheritEnv": false,
		"terminal.integrated.enableMultiLinePasteWarning": false,
		"terminal.integrated.shellIntegration.enabled": true,
		"terminal.integrated.environmentChangesIndicator": "on",
		"terminal.integrated.shellIntegration.suggestEnabled": true,
		"terminal.integrated.stickyScroll.enabled": true
	},
	"extensions": {
		"recommendations": [
			"dbaeumer.vscode-eslint",
			"ms-vscode-remote.remote-containers"
		]
	}
}