import LegalPage, { List, Paragraph, Section } from '../../components/layout/LegalPage'

export default function AboutPage() {
  return (
    <LegalPage
      title="About ExamSlot"
      intro="ExamSlot lets students plan their own exam date sheet, within rules that keep it fair and clear."
    >
      <Section heading="What it does">
        <Paragraph>
          The exam office sets up branches, courses and exam times, and creates each student&apos;s account. Each
          student then chooses where they will sit their papers, picks one exam time for every course, and saves a
          date sheet they can print or download. ExamSlot stops two exams from overlapping, keeps every choice to the
          times the exam office created, and makes each decision final unless the exam office approves one change.
        </Paragraph>
      </Section>

      <Section heading="How it works">
        <ol className="list-decimal space-y-2 ps-5 text-base leading-7 text-muted">
          <li>The exam office creates your account and you receive an email to set your password.</li>
          <li>You choose your exam branch once.</li>
          <li>You pick a time for each of your courses and review your date sheet.</li>
          <li>
            You save it once, then print it or download it. If something must change, you ask through Need help.
          </li>
        </ol>
      </Section>

      <Section heading="Credits">
        <Paragraph>ExamSlot is a demonstration with invented data.</Paragraph>
        <Paragraph>Built by Usman Ali for Loopverse 3.0.</Paragraph>
        <List
          items={[
            'Fonts: Source Serif 4 and Public Sans, under the SIL Open Font License 1.1.',
            'Icons: Lucide, under the ISC license.',
          ]}
        />
      </Section>
    </LegalPage>
  )
}
