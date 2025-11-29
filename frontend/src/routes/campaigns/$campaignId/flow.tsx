import { createFileRoute } from '@tanstack/react-router'
import { CampaignFlow } from '@/components/campaign-flow/CampaignFlow'

export const Route = createFileRoute('/campaigns/$campaignId/flow')({
  component: CampaignFlowPage,
})

function CampaignFlowPage() {
  const { campaignId } = Route.useParams()

  return <CampaignFlow campaignId={campaignId} />
}
