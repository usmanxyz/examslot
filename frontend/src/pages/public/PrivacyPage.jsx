import LegalPage, { Paragraph, Section, Table } from '../../components/layout/LegalPage'

const COLLECTED = [
  [
    'Student details: full name, email, phone, CNIC or B-Form number, date of birth, gender, address; guardian name, CNIC, occupation, contact number and emergency contact; registration number, program, semester, session, previous qualification, previous institute, marks or CGPA',
    'Entered by an administrator',
    'To identify the student, show their record and produce their date sheet',
  ],
  ['Photo (optional)', 'Uploaded by an administrator', "To show on the student's record"],
  [
    'Account email and an encrypted form of the password',
    'Entered by an administrator; the password is set by the student',
    'To let the student sign in',
  ],
  [
    'Exam branch, chosen exam times, change requests and administrator remarks',
    "Your actions and the exam office's decisions",
    'To plan and manage the date sheet',
  ],
  ['Last sign-in time', 'Recorded when you sign in', 'To help the exam office support accounts'],
  [
    'Your internet address (IP address)',
    'Every request',
    'Held briefly in memory to limit repeated attempts; never stored',
  ],
]

const PROCESSORS = [
  ['Vercel', 'Serves the website'],
  ['Render', 'Runs the application server, in its Singapore region'],
  ['Neon', 'Hosts the database, in its Singapore region'],
  ['Resend', "Delivers ExamSlot's emails"],
  ['GitHub', 'Stores encrypted weekly backups of the database'],
]

export default function PrivacyPage() {
  return (
    <LegalPage title="Privacy Policy" updated="9 October 2026">
      <Section heading="Who we are">
        <Paragraph>
          ExamSlot is a demonstration exam date sheet system built and operated by Sajjad and team in Pakistan for the
          Loopverse 3.0 hackathon. You can reach us at{' '}
          <a href="mailto:f2024266406@umt.edu.pk" className="text-primary">
            f2024266406@umt.edu.pk
          </a>
          .
        </Paragraph>
      </Section>

      <Section heading="Please use invented details">
        <Paragraph>
          ExamSlot is a demonstration. Its records are invented, and we ask everyone who tries it to use invented
          details too.
        </Paragraph>
      </Section>

      <Section heading="What we collect">
        <Table columns={['Information', 'Where it comes from', 'Why we hold it']} rows={COLLECTED} />
        <Paragraph>
          We do not collect anything else. We do not use analytics, advertising, tracking pixels or cookies.
        </Paragraph>
      </Section>

      <Section heading="How we use it">
        <Paragraph>
          We use this information only to run ExamSlot: to create accounts and send password links, to let students
          sign in, choose a branch and plan their exams, to handle change requests, to email decisions about those
          requests, and to keep the service secure.
        </Paragraph>
      </Section>

      <Section heading="Who processes it for us">
        <Table columns={['Provider', 'What it does']} rows={PROCESSORS} />
        <Paragraph>
          These providers process the data on our behalf to run ExamSlot. Some of them operate outside Pakistan. We do
          not sell or share personal information with anyone else.
        </Paragraph>
      </Section>

      <Section heading="How long we keep it">
        <Paragraph>
          The demonstration database and all accounts are deleted within 30 days after Loopverse 3.0 judging ends.
          Encrypted backups are deleted automatically 28 days after they are made. Resend keeps records of sent emails
          for 30 days.
        </Paragraph>
      </Section>

      <Section heading="How we protect it">
        <Paragraph>
          Passwords and password links are stored only in encrypted (hashed) form. Connections use HTTPS.
          Administrators and students have separate accounts. Students can see only their own information. Our logs do
          not contain personal details.
        </Paragraph>
      </Section>

      <Section heading="What is stored in your browser">
        <Paragraph>
          ExamSlot keeps your theme choice (light, dark or system) in your browser&apos;s local storage, and your
          sign-in session in your browser&apos;s session storage, which is cleared when you sign out or close the
          browser. There are no cookies.
        </Paragraph>
      </Section>

      <Section heading="Your choices">
        <Paragraph>
          You can see your own details after signing in. To correct details, ask the exam office (the administrator).
          To have your information deleted before the demonstration ends, or to ask what we hold about you, email
          f2024266406@umt.edu.pk from the address on the account.
        </Paragraph>
      </Section>

      <Section heading="Changes to this policy">
        <Paragraph>
          If this policy changes, the new version will be posted on this page with a new &quot;Last updated&quot;
          date.
        </Paragraph>
      </Section>
    </LegalPage>
  )
}
