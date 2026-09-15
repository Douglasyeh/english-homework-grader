import styles from "./page.module.css";

export default function Home() {
  return (
    <main className={styles.main}>
      <h1>English Homework Grader</h1>
      <button type="button">Upload Homework</button>
    </main>
  );
}
