import LegalPage, { List, Paragraph, Section } from '../../components/layout/LegalPage'

const EMAIL = 'f2024266406@umt.edu.pk'

export default function ContactPage() {
  return (
    <LegalPage title="Contact" updated="9 October 2026" intro="ExamSlot is run by Sajjad Zaidi">
      <Section heading="Email">
        <Paragraph>
          <a href={`mailto:${EMAIL}`} className="text-primary">
            {EMAIL}
          </a>
        </Paragraph>
        <Paragraph>When you write, please include:</Paragraph>
        <List
          items={[
            'what you were trying to do;',
            'the page you were on;',
            'the time it happened, if something went wrong.',
          ]}
        />
      </Section>

      <Section heading="Students">
        <Paragraph>
          To change your exam branch or your date sheet, sign in and use Need help. The exam office reviews every
          request.
        </Paragraph>
      </Section>

      <Section heading="Security issues">
        <Paragraph>
          If you find a security problem, email {EMAIL} with &quot;Security&quot; in the subject line. Please do not
          test it against other people&apos;s accounts.
        </Paragraph>
      </Section>

      <Section heading="Deleting your information">
        <Paragraph>Email {EMAIL} from the address on the account.</Paragraph>
      </Section>
    </LegalPage>
  )
}
