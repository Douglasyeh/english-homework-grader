# Product spec

## Product

English Homework Grader

## Primary user

English teachers.

## Core problem

Teachers spend significant time manually checking student English homework.

## Goal (MVP)

Help teachers grade scanned homework faster while keeping recognition honest: the system records what the student actually wrote, grades that text against the answer key, and sends unclear handwriting to manual review instead of guessing.

## MVP workflow

1. Teacher selects the textbook/course manually from a menu.
2. Teacher selects the unit/assignment manually.
3. Teacher uploads a scanned PDF containing homework from one or multiple students.
4. Each student's homework starts with a first page containing the student's handwritten name.
5. The system separates the uploaded pages into individual students.
6. The system extracts each student's written answers.
7. The system evaluates recognition confidence.
8. If recognition confidence is too low, the answer must be marked **需人工辨識**.
9. Recognized answers are compared against the answer key using the grading rules for that question type.
10. The teacher reviews the results.
11. The teacher can manually correct recognition or grading results before finalizing.

## Important MVP decisions

- Textbook recognition will **not** be automatic.
- Teachers manually choose the textbook.
- Teachers manually choose the unit/assignment.
- Do **not** build automatic textbook detection.
- Student separation should primarily use the handwritten student name on the first page of each student's homework.
- One uploaded PDF may contain multiple students.
- Recognition and grading are separate stages and must not be merged.
- The system must preserve what the student actually wrote.
- The recognition system must **not** silently correct a student's spelling based on the answer key.
- Low-confidence handwriting must be sent to manual review rather than guessed.
- Young students often write outside the printed answer blank. Canonical template coordinates stay tight on the expected blank; runtime crops may add padding and later ink-aware expansion, limited by a max region. Overflow must not silently steal a neighboring answer.

## Out of scope for this documentation step

Implementation of OCR, AI APIs, database code, authentication, and PDF processing is not part of this spec update. Those remain later engineering work.

## Validation Notes

The workflow has already been manually tested against real student homework from multiple textbook levels.

Those tests showed:

- Handwriting can sometimes be confidently recognized.
- Some handwriting is ambiguous.
- Answer-key knowledge can bias recognition incorrectly.
- Therefore recognition confidence and manual review are required.
- Multiple students can be processed from a single scanned batch.
- Different question formats require different grading strategies.

This document does not include student names or other personal information from those tests.
