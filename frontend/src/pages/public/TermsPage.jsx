import LegalPage, { List, Paragraph, Section } from '../../components/layout/LegalPage'

export default function TermsPage() {
  return (
    <LegalPage title="Terms and Conditions" updated="9 October 2026">
      <Section heading="1. About these terms">
        <Paragraph>
          These terms apply to ExamSlot, a web application for planning exam date sheets. ExamSlot was built and is
          operated by Usman Ali in Pakistan for the Loopverse 3.0 hackathon. By using ExamSlot you agree to these
          terms. If you do not agree, please do not use it.
        </Paragraph>
      </Section>

      <Section heading="2. What ExamSlot is">
        <Paragraph>
          ExamSlot is a demonstration. It shows how a university&apos;s exam office could let students choose their
          exam branch and exam times within set rules. It is not run for, affiliated with, or endorsed by any
          university or college. The branches, courses, exam times and student records in it are invented for the
          demonstration.
        </Paragraph>
      </Section>

      <Section heading="3. Accounts">
        <Paragraph>
          Student accounts are created by an administrator. There is no public sign-up. Keep your password private and
          do not let anyone else use your account. Accounts can be deactivated if they are misused.
        </Paragraph>
      </Section>

      <Section heading="4. Acceptable use">
        <Paragraph>When you use ExamSlot, you agree not to:</Paragraph>
        <List
          items={[
            'try to get into accounts or data that are not yours;',
            'test, scan or attack the service beyond ordinary use;',
            'enter real personal details of another person without their permission;',
            'use the administrator tools to send emails to people who did not ask for them;',
            "copy the service's data in bulk with automated tools.",
          ]}
        />
      </Section>

      <Section heading="5. Demonstration data">
        <Paragraph>
          Data in ExamSlot can be changed, reset or deleted at any time without notice. Do not use ExamSlot to plan
          real exams or to store information you need to keep.
        </Paragraph>
      </Section>

      <Section heading="6. Availability">
        <Paragraph>
          ExamSlot runs on free hosting plans. After a quiet period the server goes to sleep, so the first request can
          take up to a minute. We do not promise that ExamSlot will be available at any particular time.
        </Paragraph>
      </Section>

      <Section heading="7. Ownership">
        <Paragraph>
          The ExamSlot code, design and text are the work of Usman Ali. The fonts Source Serif 4 and Public Sans are
          used under the SIL Open Font License 1.1, and the icons come from Lucide under the ISC license.
        </Paragraph>
      </Section>

      <Section heading="8. No warranty and limited liability">
        <Paragraph>
          ExamSlot is provided as it is, without any warranty. To the extent the law allows, we are not responsible
          for any loss that comes from using it or from not being able to use it.
        </Paragraph>
      </Section>

      <Section heading="9. Ending the service">
        <Paragraph>
          The demonstration will be taken down, and its database and all accounts deleted, within 30 days after
          Loopverse 3.0 judging ends.
        </Paragraph>
      </Section>

      <Section heading="10. Changes to these terms">
        <Paragraph>
          If these terms change, the new version will be posted on this page with a new &quot;Last updated&quot; date.
        </Paragraph>
      </Section>

      <Section heading="11. Governing law">
        <Paragraph>These terms are governed by the laws of Pakistan.</Paragraph>
      </Section>

      <Section heading="12. Contact">
        <Paragraph>
          Questions about these terms:{' '}
          <a href="mailto:theusmanasghar@gmail.com" className="text-primary">
            theusmanasghar@gmail.com
          </a>
          .
        </Paragraph>
      </Section>
    </LegalPage>
  )
}
