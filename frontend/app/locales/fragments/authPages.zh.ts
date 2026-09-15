/** auth 命名空间扩展 — 注册 / 找回密码 / SSO 回调 */
export default {
  auth: {
    // 校验 / 表单
    pleaseEnterEmail: '请输入邮箱地址',
    emailPlaceholder: '请输入您的邮箱地址',
    pleaseEnterCode: '请输入验证码',
    needDomainOrEmail: '请输入域名或直接输入完整邮箱',
    passwordMinLength: '密码至少 8 位',
    passwordRules: '密码必须包含大写字母、小写字母和数字',
    passwordMismatch: '两次输入的密码不一致',
    passwordPlaceholder: '至少8位，含大小写和数字',
    confirmPasswordPlaceholder: '再次输入密码',
    codeMustBe6Digits: '验证码为6位数字',
    pleaseEnterNewPassword: '请输入新密码',
    domain: '域名',

    // 验证码流程
    codeSent: '验证码已发送到您的邮箱',
    codeResent: '验证码已重新发送',
    sendCodeFailed: '发送验证码失败，请重试',
    codeInvalid: '验证码错误',
    verifySuccess: '验证成功！',
    verifyEmail: '验证邮箱',
    verifyEmailHint: '请先验证您的外部邮箱地址',
    codeWillSendToEmail: '我们将发送验证码到此邮箱',
    codeSentToPrefix: '验证码已发送至',
    codePlaceholder: '6位验证码',
    verifying: '验证中...',
    verifiedNext: '验证成功，下一步',
    verifiedEmail: '已验证: {{email}}',
    sending: '发送中...',
    resend: '重新发送',
    back: '返回',
    backToPrevious: '返回上一步',

    // 注册
    registerFailed: '注册失败，请重试',
    displayName: '显示名称',
    displayNamePlaceholder: '显示名称（可选）',
    emailPrefixPlaceholder: '输入邮箱前缀',
    fullEmailPreview: '您的完整邮箱地址: {{email}}',
    inviteCodeLabel: '邀请码',
    inviteCodePlaceholder: '请输入邀请码',
    appEmailLabel: '{{app}} 邮箱',

    // 找回密码
    resetPasswordFailed: '重置密码失败',
    resetting: '重置中...',
    resetSuccess: '密码重置成功',
    resetSuccessHint: '您现在可以使用新密码登录了',
    rememberPassword: '想起密码了？',

    ssoLoginFailed: 'SSO 登录请求失败',

    // SSO 回调
    ssoCallback: {
      loggingIn: 'SSO 登录中',
      missingCode: '缺少授权码参数，请重新发起 SSO 登录',
      loginFailed: 'SSO 登录失败，请稍后重试',
      completing: '正在完成 SSO 登录，请稍候...',
      failedTitle: '登录失败',
    },
  },
}
