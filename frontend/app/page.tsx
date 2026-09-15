"use client";

import { FormEvent, useState } from "react";
import styles from "./page.module.css";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type UploadState = "idle" | "uploading" | "success" | "error";

type UploadResult = {
  textbook_id: string;
  unit_id: string;
  filename: string;
  page_count: number;
};

export default function Home() {
  const [selectedName, setSelectedName] = useState("");
  const [state, setState] = useState<UploadState>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [result, setResult] = useState<UploadResult | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const uploaded = formData.get("file");
    if (!(uploaded instanceof File) || uploaded.size === 0 || !uploaded.name) {
      setState("error");
      setErrorMessage("Select a PDF file first.");
      setResult(null);
      return;
    }

    setState("uploading");
    setErrorMessage("");
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/api/submissions/upload`, {
        method: "POST",
        body: formData,
      });
      const body = await response.json().catch(() => null);
      if (!response.ok) {
        const detail =
          body && typeof body.detail === "string"
            ? body.detail
            : "Upload failed.";
        setState("error");
        setErrorMessage(detail);
        return;
      }
      setResult({
        textbook_id: body.textbook_id,
        unit_id: body.unit_id,
        filename: body.filename,
        page_count: body.page_count,
      });
      setState("success");
    } catch {
      setState("error");
      setErrorMessage("Could not reach the backend.");
    }
  }

  return (
    <main className={styles.main}>
      <h1>English Homework Grader</h1>
      <form className={styles.form} onSubmit={onSubmit}>
        <label>
          Textbook
          <select name="textbook_id" defaultValue="magic-joy-5">
            <option value="magic-joy-5">Magic Joy 5</option>
          </select>
        </label>
        <label>
          Unit
          <select name="unit_id" defaultValue="unit-1">
            <option value="unit-1">Unit 1</option>
          </select>
        </label>
        <label>
          Homework PDF
          <input
            type="file"
            name="file"
            accept="application/pdf,.pdf"
            onChange={(event) => {
              const nextFile = event.target.files?.[0];
              setSelectedName(nextFile ? nextFile.name : "");
              setResult(null);
              setErrorMessage("");
              setState("idle");
            }}
          />
        </label>
        <p className={styles.status}>
          {state === "uploading"
            ? "Uploading…"
            : selectedName
              ? `Selected: ${selectedName}`
              : "No file selected"}
        </p>
        <button type="submit" disabled={state === "uploading"}>
          Upload Homework
        </button>
      </form>
      {state === "error" ? (
        <p className={styles.error} role="alert">
          {errorMessage}
        </p>
      ) : null}
      {state === "success" && result ? (
        <section className={styles.result}>
          <h2>Upload result</h2>
          <p>Textbook: {result.textbook_id}</p>
          <p>Unit: {result.unit_id}</p>
          <p>File: {result.filename}</p>
          <p>PDF page count: {result.page_count}</p>
        </section>
      ) : null}
    </main>
  );
}
