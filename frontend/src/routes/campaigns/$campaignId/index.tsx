import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Play } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useCampaignSpec, useUpdateCampaignSpec } from '@/lib/api/hooks/useCampaignSpecs'
import { useTargetGroups } from '@/lib/api/hooks/useTargetGroups'
import { useGetOrCreateCampaign } from '@/lib/api/hooks/useCampaigns'

export const Route = createFileRoute('/campaigns/$campaignId/')({
  component: EditCampaign,
})

function EditCampaign() {
  const navigate = useNavigate()
  const { campaignId } = Route.useParams()
  const { data: campaign, isLoading: campaignLoading, isError } = useCampaignSpec(campaignId)
  const { data: targetGroups = [], isLoading: targetGroupsLoading } = useTargetGroups()
  const updateCampaignSpec = useUpdateCampaignSpec()
  const getOrCreateCampaign = useGetOrCreateCampaign()

  // Form state
  const [campaignName, setCampaignName] = useState('')
  const [basePrompt, setBasePrompt] = useState('')
  const [selectedTargetGroups, setSelectedTargetGroups] = useState<string[]>([])
  const [maxIterations, setMaxIterations] = useState('2')

  // Update form state when campaign data loads
  useEffect(() => {
    if (campaign) {
      setCampaignName(campaign.name)
      setBasePrompt(campaign.base_prompt)
      setSelectedTargetGroups(campaign.target_group_ids)
      setMaxIterations(campaign.max_iterations.toString())
    }
  }, [campaign])

  const toggleTargetGroup = (id: string) => {
    setSelectedTargetGroups(prev =>
      prev.includes(id)
        ? prev.filter(groupId => groupId !== id)
        : [...prev, id]
    )
  }

  const handleUpdateCampaign = () => {
    if (!campaignName.trim() || !basePrompt.trim() || selectedTargetGroups.length === 0) {
      return
    }

    updateCampaignSpec.mutate({
      id: campaignId,
      data: {
        name: campaignName.trim(),
        base_prompt: basePrompt.trim(),
        target_group_ids: selectedTargetGroups,
        max_iterations: parseInt(maxIterations),
      }
    }, {
      onSuccess: () => {
        navigate({ to: '/campaigns' })
      }
    })
  }

  const handleStartCampaign = () => {
    // Save any changes first, then get or create campaign instance
    const saveAndStart = () => {
      getOrCreateCampaign.mutate(campaignId, {
        onSuccess: (campaignInstance) => {
          // Navigate to flow visualization using the campaign instance ID
          navigate({ to: '/campaigns/$campaignId/flow', params: { campaignId: campaignInstance.id } })
        }
      })
    }

    if (campaignName.trim() && basePrompt.trim() && selectedTargetGroups.length > 0) {
      updateCampaignSpec.mutate({
        id: campaignId,
        data: {
          name: campaignName.trim(),
          base_prompt: basePrompt.trim(),
          target_group_ids: selectedTargetGroups,
          max_iterations: parseInt(maxIterations),
        }
      }, {
        onSuccess: saveAndStart
      })
    } else {
      saveAndStart()
    }
  }

  if (campaignLoading || targetGroupsLoading) {
    return (
      <div className="max-w-screen-lg mx-auto">
        <p>Loading campaign...</p>
      </div>
    )
  }

  if (isError || !campaign) {
    return (
      <div className="max-w-screen-lg mx-auto space-y-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate({ to: '/campaigns' })}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Campaign Not Found</h1>
          </div>
        </div>
        <div className="rounded-lg border bg-card p-12">
          <div className="text-center text-muted-foreground">
            <p className="text-lg mb-2">Campaign not found</p>
            <p className="text-sm">
              The campaign you're looking for doesn't exist or has been deleted
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-screen-lg mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate({ to: '/campaigns' })}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">Edit Campaign</h1>
          <p className="text-muted-foreground mt-2">
            Update campaign settings and start generation
          </p>
        </div>
        <Button onClick={handleStartCampaign} disabled={getOrCreateCampaign.isPending || updateCampaignSpec.isPending}>
          <Play className="h-4 w-4 mr-2" />
          {getOrCreateCampaign.isPending ? 'Starting...' : 'Start Campaign'}
        </Button>
      </div>

      <div className="rounded-lg border bg-card p-6">
        <div className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="name">Campaign Name</Label>
            <Input
              id="name"
              placeholder="e.g., Running Shoes Launch"
              value={campaignName}
              onChange={(e) => setCampaignName(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="prompt">Base Prompt</Label>
            <Textarea
              id="prompt"
              placeholder="Enter the base prompt for image generation..."
              value={basePrompt}
              onChange={(e) => setBasePrompt(e.target.value)}
              rows={6}
            />
            <p className="text-xs text-muted-foreground">
              This prompt will be used as the starting point for generating
              campaign images
            </p>
          </div>

          <div className="space-y-2">
            <Label>Target Groups</Label>
            <div className="rounded-lg border bg-card p-4 space-y-2">
              {targetGroups.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No target groups available. Create target groups first.
                </p>
              ) : (
                targetGroups.map((tg) => (
                  <label
                    key={tg.id}
                    className="flex items-center gap-2 p-2 rounded hover:bg-accent cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedTargetGroups.includes(tg.id)}
                      onChange={() => toggleTargetGroup(tg.id)}
                      className="w-4 h-4"
                    />
                    <span className="text-sm">{tg.name}</span>
                  </label>
                ))
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Select one or more target groups for this campaign
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="iterations">Max Iterations</Label>
            <Input
              id="iterations"
              type="number"
              min="1"
              max="10"
              value={maxIterations}
              onChange={(e) => setMaxIterations(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Number of optimization cycles to run (recommended: 2-3)
            </p>
          </div>

          <div className="flex gap-2 pt-4">
            <Button
              variant="outline"
              onClick={() => navigate({ to: '/campaigns' })}
            >
              Cancel
            </Button>
            <Button onClick={handleUpdateCampaign} disabled={updateCampaignSpec.isPending}>
              {updateCampaignSpec.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
