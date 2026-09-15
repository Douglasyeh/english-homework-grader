# Question schema

This is a **conceptual** schema for the MVP. It is not a database implementation.

Entities below describe how homework, answers, recognition, and grading relate. Field lists are the minimum needed to support the confirmed workflow; storage types and table names can be decided later.

## Entities

### Course / Textbook

A textbook or course the teacher selects from a menu.

- `course_id`
- name / title
- (optional later) level or publisher metadata

Teachers choose this manually. The system does not detect the textbook from the scan.

### Unit

A unit inside a course/textbook.

- `unit_id`
- `course_id`
- name / number

### Assignment

A specific homework set the teacher selects (often a unit worksheet or exercise).

- `assignment_id`
- `unit_id` (and thereby `course_id`)
- name
- grading/assignment rules that apply to questions in this set, if any

### Question

A single item on an assignment.

Minimum fields:

- `question_id`
- `assignment_id`
- `question_number`
- `question_type`
- `response_mode`
- `grading_strategy`
- `expected_answer`
- `page_number` (page of the assignment template / student packet where this question appears)
- `answer_regions` (one or more page locations: handwriting blanks **or** selectable printed options)

These three fields are **not** the same thing:

| Field | Meaning |
| --- | --- |
| `question_type` | What kind of exercise this is (worksheet activity). |
| `response_mode` | How the student physically answers on the page. |
| `grading_strategy` | How the detected answer is evaluated against the key. |

Supported `response_mode` values:

1. `circle_selection` — student circles a printed option.
2. `check_selection` — student checks/selects a printed option or image.
3. `handwriting` — student writes text in one or more answer regions.

Conceptual mappings from current `question_type` values:

| question_type | response_mode |
| --- | --- |
| `listen_and_circle` | `circle_selection` |
| `listen_and_check` | `check_selection` |
| `listen_and_choose` | `check_selection` |
| `read_and_check` | `check_selection` |
| `fill_in` | `handwriting` |
| `look_and_write` | `handwriting` |

The mapping is documentation for known worksheet styles. A future question could reuse a type with a different mode only if the worksheet actually works that way; do not infer mode from type in code as if they were one field.

`grading_strategy` still selects how the grading engine compares the **Student Response** to `expected_answer` (see `docs/grading-rules.md`). It does not describe circling vs handwriting.

For multi-blank handwriting questions, `expected_answer` should be structured so each blank can be stored and graded independently (for example a list aligned with `blank_number`), rather than a single opaque sentence.

### Answer Key

The expected correct content for a question, plus any strategy-specific rules.

- `answer_key_id`
- `question_id`
- expected value(s)
- strategy-specific details (for example accepted options, per-blank keys, sentence comparison rules)

In a simple model, answer-key data may live on the Question as `expected_answer` plus `grading_strategy`. It is listed as its own concept so keys can grow without mixing them into recognition data.

### Student

A learner whose work appears in a submission.

- `student_id`
- display name (from roster or from recognized handwritten name, after review)
- (optional later) class / course membership

Identity in the MVP starts from the handwritten name on the first page of that student's homework in the scan.

### Submission

One teacher upload of a scanned PDF for a chosen assignment. The PDF may contain one or many students.

- `submission_id`
- `assignment_id`
- `course_id` / textbook as selected by the teacher
- original file reference
- uploaded-at / status (processing, needs review, finalized — exact status set later)

### Submission Page

One page extracted from the uploaded PDF.

- `page_id`
- `submission_id`
- `page_index` (order in the PDF)
- `student_id` (once student boundaries are assigned)
- image or file reference for that page
- whether this page is the first page of that student's homework (name page)

### Student Answer

What a student produced for one question (or one blank), plus recognition and grading fields. The student's writing is preserved here.

Minimum fields:

- `student_answer_id`
- `submission_id`
- `student_id`
- `question_id`
- `raw_recognized_text` — what recognition reported the student wrote
- `normalized_text` — optional derived form used only as a grading input when a strategy needs it (for example case folding). Must not replace raw text.
- `recognition_confidence`
- `recognition_status`
- `grading_status`
- `teacher_corrected_text` (optional)
- `final_result`

For multi-blank questions, store one Student Answer per blank (or an equivalent per-blank structure) so blanks are independent.

### Recognition Result

The output of the recognition stage for an answer region. May be stored on Student Answer or as a child record.

Conceptual payload:

- `raw_text`
- `confidence`
- `recognition_status`
- `metadata` (provider-agnostic details; provider name should not leak into grading)

### Grading Result

The output of the grading stage.

Conceptual payload:

- `grading_status`
- comparison details (expected vs graded text)
- whether the grade is automatic or teacher-overridden
- `final_result` after teacher review

## Status values

### Recognition status

- `recognized` — confidence is high enough to use the raw text for grading
- `needs_manual_review` — shown as **需人工辨識**; do not guess

### Grading status

- `correct`
- `incorrect`
- `needs_manual_review`
- `not_graded`

Typical flow: low-confidence recognition stays `needs_manual_review` on recognition and `not_graded` (or `needs_manual_review`) on grading until the teacher supplies text or a decision.

## Why raw recognized text must never be overwritten

`raw_recognized_text` is the system's record of **what the student actually wrote**, as read from the page.

Normalized text and teacher corrections are separate layers:

- Normalization is a derived grading aid (for example case-insensitive compare). Overwriting raw text would hide the original recognition and make it impossible to audit bias or mistakes.
- Teacher-corrected text is an explicit human edit. It must sit in `teacher_corrected_text`, not replace the recognition output.
- The answer key must never be written back into the raw field. That would silently "correct" the student (for example `bon't` → `don't`) and merge recognition with grading.

Final grading may use teacher-corrected text when present, otherwise raw (or normalized-from-raw) text — but the original recognition string stays stored.

## Relationships (conceptual)

```
Course/Textbook
  └── Unit
        └── Assignment
              ├── Question ── Answer Key
              └── Submission
                    ├── Submission Page (ordered; grouped by Student)
                    └── Student Answer
                          ├── Recognition Result
                          └── Grading Result
```

Student is linked through Submission Pages (name on first page) and Student Answers.

## JSON assignment template format

Machine-readable templates live under `data/textbooks/`, not in the database.

Current files:

- `data/textbooks/magic-joy-5/textbook.json` — textbook id, title, and unit list
- `data/textbooks/magic-joy-5/units/unit-1/assignment.json` — Unit 1 assignment import format

`textbook.json` identifies the course the teacher will pick from a menu. `assignment.json` is the import format for one unit/assignment: ids, sections, and a `questions` array.

Magic Joy 5 Unit 1 questions and answer keys are **not** stored yet. The Unit 1 file is a valid empty template (`questions: []`) until real source material is supplied. Do not copy the documentation examples below into production data as if they were textbook content.

### Assignment object

- `assignment_id`, `textbook_id`, `unit_id`
- `title`
- `sections` — ordered list (MVP: A–F as objects with `section_id` / `title`)
- `questions` — list of question objects (may be empty)
- `supported_question_types` — types the file may contain: `listen_and_circle`, `listen_and_check`, `listen_and_choose`, `read_and_check`, `fill_in`, `look_and_write`
- `supported_response_modes` — `circle_selection`, `check_selection`, `handwriting`

### Question object

Populated questions require:

- `question_id`
- `section`
- `question_number`
- `question_type`
- `response_mode`
- `grading_strategy`
- `expected_answer`
- `page_number`
- `answer_regions`
- `notes`

`assignment_id` is implied by the parent file; it does not need to be repeated on every question in the JSON template.

### Why answer regions are stored separately

`expected_answer` is the question-level answer key. `answer_regions` are on-page targets used for **response detection**.

They are stored separately because:

- Detection and confidence run on **image regions**, not on the whole question.
- What a region means depends on `response_mode` (handwriting blank vs printed selectable option).
- A question may have **one or many** regions.
- Each region has a unique `region_id` within the question.
- Coordinates (`x`, `y`, `width`, `height`) can be filled later; they may be `null` until page mapping exists.

#### Handwriting regions

Each blank has its own answer region. Each blank later gets its own raw recognized text, confidence, recognition status, and grading result.

Do not store only a finished sentence. Keep one expected value per blank and one region per blank.

Example shape (not real Magic Joy 5 content):

```json
{
  "question_id": "PLACEHOLDER_NOT_REAL_E4",
  "section": "E",
  "question_number": "4",
  "question_type": "look_and_write",
  "response_mode": "handwriting",
  "grading_strategy": "multi_blank",
  "expected_answer": ["Do", "don't"],
  "page_number": null,
  "answer_regions": [
    {
      "region_id": "PLACEHOLDER_NOT_REAL_E4_b1",
      "blank_number": 1,
      "x": null,
      "y": null,
      "width": null,
      "height": null
    },
    {
      "region_id": "PLACEHOLDER_NOT_REAL_E4_b2",
      "blank_number": 2,
      "x": null,
      "y": null,
      "width": null,
      "height": null
    }
  ],
  "notes": "PLACEHOLDER EXAMPLE — not Magic Joy 5 content"
}
```

Blank 1 maps to `Do` and region `..._b1`. Blank 2 maps to `don't` and region `..._b2`. Later, handwriting recognition reads each region independently.

#### Selection regions

For `circle_selection` and `check_selection`, regions are **selectable printed choices**, not handwriting boxes.

Each option should conceptually support:

- `option_id`
- `label` (optional printed text or description)
- region coordinates
- `expected_selected`

Example shape (not real Magic Joy 5 content): a listen-and-circle item with printed words `ping` / `pink`:

```json
{
  "question_id": "PLACEHOLDER_NOT_REAL_CIRCLE",
  "section": "A",
  "question_number": "1",
  "question_type": "listen_and_circle",
  "response_mode": "circle_selection",
  "grading_strategy": "exact_answer",
  "expected_answer": { "selected": ["option_2"] },
  "page_number": null,
  "answer_regions": [
    {
      "region_id": "PLACEHOLDER_NOT_REAL_CIRCLE_opt1",
      "option_id": "option_1",
      "label": "ping",
      "expected_selected": false,
      "x": null,
      "y": null,
      "width": null,
      "height": null
    },
    {
      "region_id": "PLACEHOLDER_NOT_REAL_CIRCLE_opt2",
      "option_id": "option_2",
      "label": "pink",
      "expected_selected": true,
      "x": null,
      "y": null,
      "width": null,
      "height": null
    }
  ],
  "notes": "PLACEHOLDER EXAMPLE — not Magic Joy 5 content"
}
```

The system later detects which printed option was circled or checked. Image/selection detection is not implemented yet.

### `expected_answer` shapes

**A. Single answer** (string):

```json
"expected_answer": "want"
```

**B. Multiple blanks** (array; index aligns with `blank_number` starting at 1):

```json
"expected_answer": ["What", "you"]
```

**C. Multiple-choice option**:

```json
"expected_answer": { "option": "A" }
```

**D. Checkbox / selected-image**:

```json
"expected_answer": {
  "selection_type": "checkbox",
  "selected": ["option_1"]
}
```

```json
"expected_answer": {
  "selection_type": "image",
  "selected": ["image_2"]
}
```

Use C/D as a question-level summary of which option(s) are correct. For selection items, also set `expected_selected` on each option region so detection can compare mark vs key per printed target. Option identifiers will come from the real worksheet when it is supplied.
