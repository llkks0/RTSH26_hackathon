import {createFileRoute, useNavigate} from '@tanstack/react-router'
import {Button} from '@/components/ui/button'
import {Pencil, Plus, Trash2} from 'lucide-react'
import {useCampaignSpecs, useDeleteCampaignSpec} from '@/lib/api/hooks/useCampaignSpecs'
import {useTargetGroups} from '@/lib/api/hooks/useTargetGroups'

export const Route = createFileRoute('/campaigns/')({
    component: Campaigns,
})

function Campaigns() {
    const navigate = useNavigate()
    const {data: campaigns = [], isLoading: campaignsLoading} = useCampaignSpecs()
    const {data: targetGroups = [], isLoading: targetGroupsLoading} = useTargetGroups()
    const deleteCampaignSpec = useDeleteCampaignSpec()

    const handleDeleteCampaign = (id: string) => {
        if (confirm('Are you sure you want to delete this campaign?')) {
            deleteCampaignSpec.mutate(id)
        }
    }

    const getTargetGroupNames = (ids: string[]) => {
        return ids.map(id =>
            targetGroups.find((tg) => tg.id === id)?.name || 'Unknown'
        ).join(', ')
    }

    if (campaignsLoading || targetGroupsLoading) {
        return (
            <div className="max-w-screen-lg mx-auto">
                <p>Loading campaigns...</p>
            </div>
        )
    }

    return (
        <div className="max-w-screen-lg mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Campaigns</h1>
                    <p className="text-muted-foreground mt-2">
                        Create and manage adaptive image generation campaigns
                    </p>
                </div>
                <Button onClick={() => navigate({to: '/campaigns/new'})}>
                    <Plus className="h-4 w-4 mr-2"/>
                    New Campaign
                </Button>
            </div>
            {
                campaigns.length === 0 ? (
                    <div className="rounded-lg border bg-card p-12">
                        <div className="text-center text-muted-foreground">
                            <p className="text-lg mb-2">No campaigns yet</p>
                            <p className="text-sm">Create your first campaign to start generating adaptive ad
                                creatives</p>
                        </div>
                    </div>
                ) : (
                    <div className="grid gap-4">
                        {campaigns.map((campaign) => (
                            <div
                                key={campaign.id}
                                className="rounded-lg border bg-card p-6 hover:border-primary/50 transition-colors"
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <h3 className="text-xl font-semibold mb-2">{campaign.name}</h3>
                                        <p className="text-sm text-muted-foreground mb-4">{campaign.base_prompt}</p>
                                        <div className="flex gap-4 text-sm">
                                            <div>
                                                <span className="text-muted-foreground">Target Groups: </span>
                                                <span
                                                    className="font-medium">{getTargetGroupNames(campaign.target_group_ids)}</span>
                                            </div>
                                            <div>
                                                <span className="text-muted-foreground">Max Iterations: </span>
                                                <span className="font-medium">{campaign.max_iterations}</span>
                                            </div>
                                            <div>
                                                <span className="text-muted-foreground">Created: </span>
                                                <span className="font-medium">
                        {new Date(campaign.created_at).toLocaleDateString()}
                      </span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => navigate({
                                                to: '/campaigns/$campaignId',
                                                params: {campaignId: campaign.id}
                                            })}
                                        >
                                            <Pencil className="h-4 w-4"/>
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => handleDeleteCampaign(campaign.id)}
                                            disabled={deleteCampaignSpec.isPending}
                                        >
                                            <Trash2 className="h-4 w-4"/>
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )
            }
        </div>
    )
}
