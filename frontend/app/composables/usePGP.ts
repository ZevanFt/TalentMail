/**
 * PGP 加密/解密 Composable（客户端 E2E）
 *
 * 使用 OpenPGP.js 在浏览器中完成加密/解密，
 * 私钥仅存储在 localStorage，服务端永远不接触。
 */

const PGP_PRIVATE_KEY_STORAGE = 'talentmail_pgp_private_key'
const PGP_PASSPHRASE_STORAGE = 'talentmail_pgp_passphrase'

interface PGPKeyPair {
  publicKey: string
  privateKey: string
  fingerprint: string
}

export const usePGP = () => {
  const hasLocalPrivateKey = computed(() => {
    if (!import.meta.client) return false
    return !!localStorage.getItem(PGP_PRIVATE_KEY_STORAGE)
  })

  /**
   * 生成新的 PGP 密钥对
   */
  const generateKeyPair = async (name: string, email: string, passphrase: string): Promise<PGPKeyPair> => {
    const openpgp = await import('openpgp')

    const { privateKey, publicKey } = await openpgp.generateKey({
      type: 'ecc',
      curve: 'curve25519',
      userIDs: [{ name, email }],
      passphrase,
      format: 'armored',
    })

    // 读取指纹
    const pubKeyObj = await openpgp.readKey({ armoredKey: publicKey })
    const fingerprint = pubKeyObj.getFingerprint().toUpperCase()

    // 存储私钥到 localStorage
    localStorage.setItem(PGP_PRIVATE_KEY_STORAGE, privateKey)
    localStorage.setItem(PGP_PASSPHRASE_STORAGE, passphrase)

    return { publicKey, privateKey, fingerprint }
  }

  /**
   * 加密消息
   */
  const encryptMessage = async (plaintext: string, recipientPublicKey: string, senderPrivateKey?: string, passphrase?: string): Promise<string> => {
    const openpgp = await import('openpgp')

    const pubKey = await openpgp.readKey({ armoredKey: recipientPublicKey })

    const options: any = {
      message: await openpgp.createMessage({ text: plaintext }),
      encryptionKeys: pubKey,
    }

    // 如果提供了发件人私钥，则签名
    if (senderPrivateKey && passphrase) {
      const privKey = await openpgp.decryptKey({
        privateKey: await openpgp.readPrivateKey({ armoredKey: senderPrivateKey }),
        passphrase,
      })
      options.signingKeys = privKey
    }

    const encrypted = await openpgp.encrypt(options)
    return encrypted as string
  }

  /**
   * 解密消息
   */
  const decryptMessage = async (encryptedText: string, passphrase?: string): Promise<string> => {
    const openpgp = await import('openpgp')

    const storedKey = localStorage.getItem(PGP_PRIVATE_KEY_STORAGE)
    if (!storedKey) throw new Error('未找到本地私钥')

    const pp = passphrase || localStorage.getItem(PGP_PASSPHRASE_STORAGE) || ''

    const privateKey = await openpgp.decryptKey({
      privateKey: await openpgp.readPrivateKey({ armoredKey: storedKey }),
      passphrase: pp,
    })

    const message = await openpgp.readMessage({ armoredMessage: encryptedText })

    const { data: decrypted } = await openpgp.decrypt({
      message,
      decryptionKeys: privateKey,
    })

    return decrypted as string
  }

  /**
   * 导入已有私钥
   */
  const importPrivateKey = (armoredKey: string, passphrase: string) => {
    localStorage.setItem(PGP_PRIVATE_KEY_STORAGE, armoredKey)
    localStorage.setItem(PGP_PASSPHRASE_STORAGE, passphrase)
  }

  /**
   * 导出本地私钥
   */
  const exportPrivateKey = (): string | null => {
    return localStorage.getItem(PGP_PRIVATE_KEY_STORAGE)
  }

  /**
   * 清除本地密钥
   */
  const clearLocalKeys = () => {
    localStorage.removeItem(PGP_PRIVATE_KEY_STORAGE)
    localStorage.removeItem(PGP_PASSPHRASE_STORAGE)
  }

  /**
   * 获取本地密钥指纹
   */
  const getLocalFingerprint = async (): Promise<string | null> => {
    const storedKey = localStorage.getItem(PGP_PRIVATE_KEY_STORAGE)
    if (!storedKey) return null
    try {
      const openpgp = await import('openpgp')
      const key = await openpgp.readPrivateKey({ armoredKey: storedKey })
      return key.getFingerprint().toUpperCase()
    } catch {
      return null
    }
  }

  return {
    hasLocalPrivateKey,
    generateKeyPair,
    encryptMessage,
    decryptMessage,
    importPrivateKey,
    exportPrivateKey,
    clearLocalKeys,
    getLocalFingerprint,
  }
}
