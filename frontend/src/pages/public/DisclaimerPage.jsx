import LegalPage, { Paragraph } from '../../components/layout/LegalPage'

export default function DisclaimerPage() {
  return (
    <LegalPage
      title="Disclaimer"
      updated="9 October 2026"
      intro="ExamSlot is a demonstration built by Usman Ali for the Loopverse 3.0 hackathon. It is not run for, affiliated with, or endorsed by any university or college."
    >
      <Paragraph>
        The branches, courses, exam times and people shown in ExamSlot are invented. Do not rely on ExamSlot for real
        exam dates, venues or arrangements. Always follow the instructions of your own institution.
      </Paragraph>
      <Paragraph>
        ExamSlot is provided as it is. Data may be reset or deleted at any time, and the service will be taken down
        within 30 days after Loopverse 3.0 judging ends.
      </Paragraph>
    </LegalPage>
  )
}
