import {createFileRoute} from '@tanstack/react-router'
import {CampaignGraph} from "@/components/campaign-graph/CampaignGraph.tsx";

export const Route = createFileRoute('/campaigns/$campaignId/flow')({
    component: CampaignFlowPage,
})

function CampaignFlowPage() {
    const {campaignId} = Route.useParams()

    return <div className="-m-6"><CampaignGraph campaignId={campaignId}/></div>
}
