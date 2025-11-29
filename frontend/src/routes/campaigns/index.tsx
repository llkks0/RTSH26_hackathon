import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Plus, Trash2, Pencil } from 'lucide-react'

export const Route = createFileRoute('/campaigns/')({
    component: Campaigns,
})

interface TargetGroup {
    id: string
    name: string
    city?: string
    ageGroup?: string
    economicStatus?: string
    description?: string
}

interface Campaign {
    id: string
    name: string
    basePrompt: string
    targetGroupIds: string[]
    maxIterations: number
    createdAt: string
}

const STORAGE_KEYS = {
    CAMPAIGNS: 'adaptive-gen-campaigns',
    TARGET_GROUPS: 'adaptive-gen-target-groups',
}

function Campaigns() {
    const navigate = useNavigate()
    const [campaigns, setCampaigns] = useState<Campaign[]>([])
    const [targetGroups, setTargetGroups] = useState<TargetGroup[]>([])

    // Load from localStorage on mount
    useEffect(() => {
        const savedCampaigns = localStorage.getItem(STORAGE_KEYS.CAMPAIGNS)
        const savedTargetGroups = localStorage.getItem(STORAGE_KEYS.TARGET_GROUPS)

        if (savedCampaigns) {
            setCampaigns(JSON.parse(savedCampaigns))
        }

        if (savedTargetGroups) {
            setTargetGroups(JSON.parse(savedTargetGroups))
        }
    }, [])

    const handleDeleteCampaign = (id: string) => {
        const updatedCampaigns = campaigns.filter((c) => c.id !== id)
        setCampaigns(updatedCampaigns)
        localStorage.setItem(STORAGE_KEYS.CAMPAIGNS, JSON.stringify(updatedCampaigns))
    }

    const getTargetGroupNames = (ids: string[]) => {
        return ids.map(id =>
            targetGroups.find((tg) => tg.id === id)?.name || 'Unknown'
        ).join(', ')
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
                <Button onClick={() => navigate({ to: '/campaigns/new' })}>
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
                                        <p className="text-sm text-muted-foreground mb-4">{campaign.basePrompt}</p>
                                        <div className="flex gap-4 text-sm">
                                            <div>
                                                <span className="text-muted-foreground">Target Groups: </span>
                                                <span
                                                    className="font-medium">{getTargetGroupNames(campaign.targetGroupIds)}</span>
                                            </div>
                                            <div>
                                                <span className="text-muted-foreground">Max Iterations: </span>
                                                <span className="font-medium">{campaign.maxIterations}</span>
                                            </div>
                                            <div>
                                                <span className="text-muted-foreground">Created: </span>
                                                <span className="font-medium">
                        {new Date(campaign.createdAt).toLocaleDateString()}
                      </span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => navigate({ to: '/campaigns/$campaignId', params: { campaignId: campaign.id } })}
                                        >
                                            <Pencil className="h-4 w-4"/>
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => handleDeleteCampaign(campaign.id)}
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
