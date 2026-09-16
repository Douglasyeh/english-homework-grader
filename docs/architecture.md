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
- One PDF may contain multiple students. Milestone 3B groups pages **by position** using `len(assignment_pages)`. Student-name detection is not used yet.
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

Turns the uploaded PDF into ordered page images, then (Milestone 3B) maps those images onto `assignment_pages` by position. Student-name boundaries and question-region clips are later steps.

Page rendering produces **images only**. It does not run OCR, selection detection, or grading.

Keep these page identifiers separate:

| Concept | Meaning | Example (Magic Joy 5 Unit 1) |
| --- | --- | --- |
| Assignment page `sequence` | 1-based position in the selected unit's homework | 1, 2, 3 |
| `workbook_page` | Printed number in the textbook | 4, 5, 6 |
| PDF `page_index` | 0-based page in the teacher upload | 0, 1, 2, … |
| Upload `page_number` | 1-based PDF display order | 1, 2, 3, … |
| Canonical template page | Blank/key worksheet image for that assignment page | `templates/MJ5-U1-P1.png` |

**Milestone 4A** adds template alignment and region crops (no recognition):

```
Uploaded PDF
→ Page PNG
→ Student Group
→ Assignment Page
→ Canonical Template
→ Page Alignment
→ Aligned Student Page
→ Answer Region Crop
→ Response Mode Router
→ Selection Detection OR Handwriting Recognition
→ Student Response
→ Grading Engine
```

Only through **Answer Region Crop** is implemented. Alignment currently returns `template_missing` when the canonical PNG is absent, or `not_aligned` if the file exists but no geometric transform has been computed. It never reports `aligned` by copying the raw student image.

Normalized region coordinates live on the **template**. `normalized_region_to_pixels` converts them for an aligned image of any size. Debug overlays draw labeled boxes (`region_id`) for human checks. They do not grade.

### Handwriting overflow and runtime crops

Young students frequently write larger than the printed blank. Ink may extend above, below, left, or right of the canonical rectangle, touch a neighbor, or span several expected word blanks.

The stored canonical region means **where the answer is expected**. It does **not** mean that pixels outside that rectangle must be ignored.

Four layers:

| Layer | Stored? | Role |
| --- | --- | --- |
| `canonical_region` | Yes (`assignment.json` `x,y,width,height`) | Verified expected location. Do not enlarge it to hide handwriting variation. |
| `padded_region` | No (derived) | Canonical plus configurable, response-mode-specific padding. |
| `ink_expanded_region` | No (derived) | Optional further growth when ink continues near the padded boundary. Geometry only; not recognition. |
| `max_region` | No (configured/derived) | Hard stop so one answer cannot consume a neighbor, unrelated text, or an illustration. |

Runtime crop answers **how much image** later recognition should inspect. Recognition later answers **what** was written. Grading later answers **whether** that is correct.

Padding defaults differ by `response_mode` (`handwriting` larger, especially above the line; `circle_selection` a modest circle margin; `check_selection` a small checkbox margin). Padding never writes back into the Golden Dataset.

If ink still continues past `max_region`, two neighboring blanks look connected, or a crop would overlap a neighbor's canonical box, the crop plan status is `needs_manual_review` (**需人工辨識**). Prefer review over silently assigning handwriting to the wrong blank. Do not auto-correct spelling.

Multi-blank questions keep per-blank canonical regions. A larger question/line **fallback region** (union of those blanks, padded at runtime) may be used later when individual crops are unreliable. It does not replace the blanks.

Student-page geometric alignment is still required before these template coordinates are applied to a raw student PNG.

`page_number` on Golden Dataset **questions** is the printed workbook page, not PDF order.

The number of homework sheets per student is derived as `len(assignment_pages)`. Do not hard-code 3 (or any other count) in application logic.

**Milestone 3B** groups uploaded PDF pages by position only:

```
Assignment
  → assignment_pages
  → expected_pages_per_student = len(assignment_pages)

Uploaded PDF
  → ordered rendered pages
  → positional grouping (repeating assignment sequences)
  → assignment_page mapping
  → provisional student groups (group-001, …)
```

This is an MVP assumption. Groups are **not** identified students. Future work may verify or replace positional grouping with student-name recognition, page classification, or manual correction. Those are not implemented here.

If `uploaded_page_count % expected_pages_per_student != 0`, grouping status is `needs_manual_review`. Complete-size chunks may appear as `provisional_groups` for later review, leftover pages as `remaining_pages`, and `student_groups` stays empty so leftovers are never treated as a finished student packet. Pages are never shifted, guessed, or dropped.

Zero `assignment_pages` does not divide; the result is `needs_manual_review` with every uploaded page in `remaining_pages`.

For Milestone 2, generated PNGs are stored in a local development directory (`EHG_STORAGE_DIR` if set, otherwise the OS temp folder under `english-homework-grader/`). Original student PDFs are not kept. This store is not a database and can be replaced later.

In upload JSON, `page_index` is 0-based PDF order and response `page_number` is currently **1-based PDF display order**. That upload field is still not the workbook page. Later, each uploaded PDF page will be associated with an `assignment_page_id` before region extraction or grading.

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
recognize_handwriting(runtime_crop) -> {
    raw_text,
    confidence,
    metadata
}
```

`runtime_crop` is the image actually inspected (padded and possibly ink-expanded, clipped to `max_region`), not a permission to mutate stored canonical coordinates.

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

Before student-page geometric alignment is implemented, remaining crop-related decisions include: exact production padding numbers per textbook, whether ink expansion runs on grayscale page images or a dedicated ink mask, how aggressively `max_region` sits between dense F-section blanks, and when to prefer the multi-blank fallback crop versus per-blank crops. Those choices do not require changing Magic Joy 5 Unit 1 canonical coordinates.
