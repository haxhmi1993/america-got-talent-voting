import { useState, FormEvent } from 'react'
import FingerprintJS from '@fingerprintjs/fingerprintjs'
import styles from '../styles/VoteForm.module.css'

interface VoteResponse {
  status: string
  message: string
  type?: string
}

export default function VoteForm() {
  const [lastName, setLastName] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' | 'challenge' } | null>(null)

  const generateNonce = (): string => {
    const timestamp = new Date().toISOString()
    const random = Math.random().toString(36).substring(2, 15)
    return `${timestamp}-${random}`
  }

  const getFingerprint = async (): Promise<string> => {
    try {
      const fp = await FingerprintJS.load()
      const result = await fp.get()
      return result.visitorId
    } catch (error) {
      console.error('Error generating fingerprint:', error)
      // Fallback fingerprint
      return `fallback-${navigator.userAgent}-${screen.width}x${screen.height}`
    }
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    
    if (!lastName.trim()) {
      setMessage({ text: 'Please enter a contestant last name', type: 'error' })
      return
    }

    setLoading(true)
    setMessage(null)

    try {
      const fingerprint = await getFingerprint()
      const nonce = generateNonce()

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      const response = await fetch(`${apiUrl}/api/vote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          last_name: lastName.trim(),
          fingerprint: fingerprint,
          nonce: nonce,
        }),
      })

      const data: VoteResponse = await response.json()

      if (response.ok) {
        if (data.status === 'success') {
          setMessage({ text: data.message, type: 'success' })
          setLastName('')
        } else if (data.status === 'challenge') {
          setMessage({ 
            text: `${data.message} (Challenge type: ${data.type})`, 
            type: 'challenge' 
          })
        }
      } else {
        setMessage({ 
          text: data.message || 'Failed to submit vote. Please try again.', 
          type: 'error' 
        })
      }
    } catch (error) {
      console.error('Error submitting vote:', error)
      setMessage({ 
        text: 'Network error. Please check your connection and try again.', 
        type: 'error' 
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.formContainer}>
      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.inputGroup}>
          <label htmlFor="lastName" className={styles.label}>
            Contestant Last Name
          </label>
          <input
            id="lastName"
            type="text"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            placeholder="Enter last name..."
            className={styles.input}
            disabled={loading}
            maxLength={255}
          />
        </div>

        <button 
          type="submit" 
          className={styles.button}
          disabled={loading || !lastName.trim()}
        >
          {loading ? 'Submitting Vote...' : 'Submit Vote'}
        </button>
      </form>

      {message && (
        <div className={`${styles.message} ${styles[message.type]}`}>
          {message.text}
        </div>
      )}
    </div>
  )
}
