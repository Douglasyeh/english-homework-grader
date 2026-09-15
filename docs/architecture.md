# Architecture

This document describes the planned MVP architecture. It does not select an OCR/AI vendor and does not specify implementation libraries.

The stack remains: Next.js (TypeScript) frontend, FastAPI backend, PostgreSQL later, REST API.

## MVP processing pipeline

```
Teacher
  ↓
Select textbook
  ↓
Select unit / assignment
  ↓
Upload scanned PDF
  ↓
PDF page extraction
  ↓
Student boundary / name detection
  ↓
Question-region extraction
  ↓
Response Detection (routed by response_mode)
  ↓
Confidence evaluation
  ↓
Manual review queue (when needed)
  ↓
Answer normalization
  ↓
Grading engine
  ↓
Teacher review
  ↓
Final results
```

Notes on the pipeline:

- Textbook and unit/assignment are teacher-selected. There is no automatic textbook detection.
- One PDF may contain multiple students. Student boundaries are based primarily on the handwritten name on the first page of each student's homework.
- Response Detection runs before grading. It is routed by `response_mode` (circle, check, or handwriting), not by `question_type`.
- Low-confidence detection is flagged for manual review (需人工辨識) rather than guessed.
- Normalization is applied to a copy/derived field for grading strategies that need it; it does not replace raw handwriting text.
- The teacher can correct detection/recognition and grading before finalizing.

## Conceptual components

### Frontend

Teacher-facing Next.js app: textbook/assignment menus, PDF upload, result review, and manual correction of recognition and grades.

### Backend API

FastAPI REST API. Orchestrates uploads, pipeline jobs, and review actions. Does not embed a specific OCR vendor into grading logic.

### Document Processing

Turns the uploaded PDF into ordered page images, groups pages by student (name-page boundaries), and (later) clips question `answer_region`s.

Page rendering produces **images only**. It does not run OCR, selection detection, or grading.

For Milestone 2, generated PNGs are stored in a local development directory (`EHG_STORAGE_DIR` if set, otherwise the OS temp folder under `english-homework-grader/`). Original student PDFs are not kept. This store is not a database and can be replaced later.

`page_index` is 0-based PDF order. `page_number` in the upload response is currently **1-based PDF display order**, not the Magic Joy workbook page printed on the sheet (4 / 5 / 6). Workbook page numbers stay on the assignment template.

### Response Detection

Takes a question's page regions and `response_mode`, then produces a **Student Response** object for the grading engine.

```
Question Region
  ↓
Response Mode Router
  ↓
if circle_selection:
    Selection Detection
  ↓
if check_selection:
    Selection Detection
  ↓
if handwriting:
    Handwriting Recognition
  ↓
Student Response
  ↓
Grading Engine
```

All paths must emit the same conceptual Student Response (detected value(s), confidence, status, optional metadata). The Grading Engine must **not** need to know whether that response came from circle detection, checkbox detection, handwriting recognition, or a future provider.

### Recognition Service

Handwriting path only: accepts an answer-region image and returns what was written, plus confidence. Behind a provider interface so the vendor can change later.

### Grading Engine

Compares the Student Response (or teacher-corrected values) to the answer key using the question's `grading_strategy`. It does not call OCR, selection detectors, or branch on `response_mode` or provider name.

### Database

PostgreSQL (later): courses, assignments, questions, answer keys, submissions, pages, students, answers, recognition and grading results. Schema is conceptual in `docs/question-schema.md`.

### Manual Review Workflow

Queue and UI for low-confidence items (**需人工辨識**) and for teacher overrides of recognition or grades before final results.

## Detection-provider interfaces (conceptual)

No OCR/AI/image vendor is selected. The rest of the system depends on stable interfaces.

Selection detection (`circle_selection` and `check_selection`):

```
detect_selection(question_region, options) -> {
    selected_option_ids,
    confidence,
    metadata
}
```

Handwriting recognition (`handwriting`):

```
recognize_handwriting(answer_region) -> {
    raw_text,
    confidence,
    metadata
}
```

- `raw_text`: what the student wrote, without answer-key spelling correction. Unreliable handwriting yields **需人工辨識** / `needs_manual_review` rather than a guess.
- `selected_option_ids`: which printed options were detected as marked. Unreliable marks go to manual review rather than a guess.
- `confidence`: used only for routing (auto-grade vs manual review). Thresholds are configurable later; none is fixed here.
- `metadata`: optional extras. Must not be required by the grading engine.

The grading engine receives a **Student Response**, not a provider name. Handwriting and selection providers can be replaced later without rewriting the grading engine.

## Stage boundary: detection vs grading

| Stage | Responsibility |
| --- | --- |
| Response mode router | Choose selection detection vs handwriting recognition |
| Selection detection | Which printed option was circled or checked? |
| Handwriting recognition | What did the student actually write in this blank? |
| Confidence evaluation | Auto-continue vs 需人工辨識 |
| Normalization | Derived values for some strategies only |
| Grading | Is the Student Response correct against the key? |
| Teacher review | Human correction, then final results |

These stages stay separate in code and in stored data. `question_type`, `response_mode`, and `grading_strategy` stay separate fields.

## What this architecture deliberately does not decide yet

See the unresolved list in the project handoff: OCR/AI provider, confidence threshold values, PDF and storage libraries, and database physical design remain open.
