# Grading rules

Recognition and grading are separate stages. They must never be merged.

## A. Recognition

Recognition answers: **What did the student actually write?**

The recognition layer reads handwriting (or other marks) from an answer region and returns the student's written content plus a confidence signal.

Rules:

- Preserve the student's writing. Do not rewrite it to match the answer key.
- Do not use the expected answer to "fix" spelling, grammar, or option letters.
- If handwriting cannot be recognized reliably, return **需人工辨識**. Do not guess.
- High-confidence recognition can proceed to automatic grading.
- Low-confidence recognition must be flagged for manual recognition.
- Confidence thresholds must be configurable later.
- Do not hard-code a final confidence threshold in this document or in early implementation.

### Example: recognition must not follow the answer key

Correct answer: `don't`

Student handwriting: `bon't`

Recognition result must be: `bon't`

The recognition layer must **not** change `bon't` into `don't` simply because `don't` exists in the answer key.

## B. Grading

Grading answers: **Is what the student wrote correct?**

The grading engine receives:

- the recognition result (or teacher-corrected text after manual review), and
- the question's answer key and grading strategy.

It does **not** re-read the handwriting and does **not** choose an OCR/AI provider.

Rules:

- Grade what was recognized (or what the teacher corrected), not what the system thinks the student "meant."
- Do not assume fuzzy spelling should automatically count as correct.
- Manual review must always be possible, including after automatic grading.
- If recognition status is needs-manual-review (需人工辨識), the item should not be treated as a confident automatic grade.

### Same example, after recognition

Recognition result: `bon't`

Expected answer: `don't`

Grading result: incorrect

## Grading strategy categories

Question types should support different grading strategies. Initial categories:

1. **Exact answer**  
   Compare the student answer to the expected answer as a fixed match.  
   Example uses: multiple choice letter, single word, other fixed answers.

2. **Case-insensitive exact answer**  
   Same as exact match, except capitalization is not important.

3. **Multi-blank answer**  
   Each blank must be stored and evaluated independently. A question may have some blanks correct and others incorrect.

4. **Sentence answer**  
   Compare against the expected sentence according to assignment rules for that question. Assignment-specific sentence rules are stored with the answer key; they are not invented at grading time.

5. **Multiple choice / checkbox**  
   Compare selected option(s) against the answer key.

6. **Listening-based questions**  
   Correctness is determined by the stored answer key. The MVP does not need to understand the audio itself during grading if the expected answer is already stored.

## Manual review

Teachers can always:

- correct recognized text,
- override a grade,
- resolve items marked **需人工辨識**,

before results are finalized.
