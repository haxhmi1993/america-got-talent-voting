import { useState } from 'react'
import Head from 'next/head'
import VoteForm from '../components/VoteForm'
import styles from '../styles/Home.module.css'

export default function Home() {
  return (
    <>
      <Head>
        <title>AGT Voting System</title>
        <meta name="description" content="America's Got Talent Voting System POC" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <main className={styles.main}>
        <div className={styles.container}>
          <h1 className={styles.title}>
            America's Got Talent
            <br />
            <span className={styles.subtitle}>Voting System</span>
          </h1>
          <p className={styles.description}>
            Vote for your favorite contestant by entering their last name below.
            <br />
            <small>You can vote up to 3 times for different contestants.</small>
          </p>
          <VoteForm />
        </div>
      </main>
    </>
  )
}
