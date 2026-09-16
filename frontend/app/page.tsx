"use client";

import { FormEvent, useState } from "react";
import styles from "./page.module.css";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type UploadState = "idle" | "uploading" | "success" | "error";

type PagePreview = {
  page_index: number;
  page_number: number;
  image_url: string;
  assignment_page_id?: string;
  assignment_page_sequence?: number;
  workbook_page?: number;
  alignment_status?: string;
  aligned_image_url?: string | null;
  debug_overlay_url?: string | null;
};

type StudentGroup = {
  student_group_id: string;
  group_number: number;
  pages: PagePreview[];
};

type UploadResult = {
  textbook_id: string;
  unit_id: string;
  filename: string;
  page_count: number;
  pages: PagePreview[];
  grouping_status: string;
  expected_pages_per_student: number;
  group_count: number;
  complete_group_count: number;
  remaining_page_count: number;
  student_groups: StudentGroup[];
  remaining_pages: PagePreview[];
};

function imageSrc(url: string): string {
  return url.startsWith("http") ? url : `${API_BASE}${url}`;
}

function PageThumb({
  page,
  caption,
}: {
  page: PagePreview;
  caption: string;
}) {
  const src = imageSrc(page.image_url);
  return (
    <figure className={styles.preview}>
      <figcaption>{caption}</figcaption>
      <a href={src} target="_blank" rel="noreferrer">
        <img src={src} alt={caption} />
      </a>
    </figure>
  );
}

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
        pages: Array.isArray(body.pages) ? body.pages : [],
        grouping_status: body.grouping_status,
        expected_pages_per_student: body.expected_pages_per_student,
        group_count: body.group_count,
        complete_group_count: body.complete_group_count,
        remaining_page_count: body.remaining_page_count,
        student_groups: Array.isArray(body.student_groups)
          ? body.student_groups
          : [],
        remaining_pages: Array.isArray(body.remaining_pages)
          ? body.remaining_pages
          : [],
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
          {result.grouping_status === "needs_manual_review" ? (
            <div className={styles.review} role="status">
              <p>Page grouping needs review.</p>
              <p>Uploaded page count: {result.page_count}</p>
              <p>
                Expected pages per student:{" "}
                {result.expected_pages_per_student}
              </p>
              <p>Complete group count: {result.complete_group_count}</p>
              <p>Remaining page count: {result.remaining_page_count}</p>
            </div>
          ) : null}
          {result.grouping_status === "grouped" ? (
            <>
              <p className={styles.debugNote}>
                Debug: alignment status is shown on each page. Region overlays
                appear only after a canonical template is aligned. Coordinates
                locate inspection areas; they are not answers.
              </p>
              {result.student_groups.map((group) => (
                <div key={group.student_group_id} className={styles.group}>
                  <h3>Student Group {group.group_number}</h3>
                  <div className={styles.previews}>
                    {group.pages.map((page) => (
                      <PageThumb
                        key={page.page_index}
                        page={page}
                        caption={`Assignment Page ${page.assignment_page_sequence} (Workbook ${page.workbook_page}) · ${page.alignment_status ?? "unknown"}`}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </>
          ) : (
            <div className={styles.previews}>
              {result.pages.map((page) => (
                <PageThumb
                  key={page.page_index}
                  page={page}
                  caption={`Page ${page.page_number}`}
                />
              ))}
            </div>
          )}
        </section>
      ) : null}
    </main>
  );
}
