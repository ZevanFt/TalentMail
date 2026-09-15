/** auth namespace extras — register / forgot password / SSO callback */
export default {
  auth: {
    // Validation / form
    pleaseEnterEmail: 'Please enter your email address',
    emailPlaceholder: 'Enter your email address',
    pleaseEnterCode: 'Please enter the verification code',
    needDomainOrEmail: 'Please enter a domain or a full email address',
    passwordMinLength: 'Password must be at least 8 characters',
    passwordRules: 'Password must contain uppercase, lowercase letters and a number',
    passwordMismatch: 'Passwords do not match',
    passwordPlaceholder: 'At least 8 chars with upper/lowercase and number',
    confirmPasswordPlaceholder: 'Enter password again',
    codeMustBe6Digits: 'Verification code must be 6 digits',
    pleaseEnterNewPassword: 'Please enter a new password',
    domain: 'Domain',

    // Verification code flow
    codeSent: 'Verification code has been sent to your email',
    codeResent: 'Verification code has been resent',
    sendCodeFailed: 'Failed to send verification code, please try again',
    codeInvalid: 'Invalid verification code',
    verifySuccess: 'Verified successfully!',
    verifyEmail: 'Email verification',
    verifyEmailHint: 'Please verify your external email address first',
    codeWillSendToEmail: 'We will send a verification code to this email',
    codeSentToPrefix: 'Code sent to',
    codePlaceholder: '6-digit code',
    verifying: 'Verifying...',
    verifiedNext: 'Verified, continue',
    verifiedEmail: 'Verified: {{email}}',
    sending: 'Sending...',
    resend: 'Resend',
    back: 'Back',
    backToPrevious: 'Back to previous step',

    // Register
    registerFailed: 'Registration failed, please try again',
    displayName: 'Display name',
    displayNamePlaceholder: 'Display name (optional)',
    emailPrefixPlaceholder: 'Enter email prefix',
    fullEmailPreview: 'Your full email: {{email}}',
    inviteCodeLabel: 'Invite code',
    inviteCodePlaceholder: 'Enter invite code',
    appEmailLabel: '{{app}} email',

    // Forgot password
    resetPasswordFailed: 'Failed to reset password',
    resetting: 'Resetting...',
    resetSuccess: 'Password reset successfully',
    resetSuccessHint: 'You can now sign in with your new password',
    rememberPassword: 'Remembered your password?',

    ssoLoginFailed: 'SSO login request failed',

    // SSO callback
    ssoCallback: {
      loggingIn: 'SSO signing in',
      missingCode: 'Missing authorization code, please start SSO login again',
      loginFailed: 'SSO login failed, please try again later',
      completing: 'Completing SSO login, please wait...',
      failedTitle: 'Login failed',
    },
  },
}
