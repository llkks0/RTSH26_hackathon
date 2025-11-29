import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

export const Route = createFileRoute('/campaigns/new')({
  component: NewCampaign,
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

function NewCampaign() {
  const navigate = useNavigate()
  const [targetGroups, setTargetGroups] = useState<TargetGroup[]>([])

  // Form state
  const [campaignName, setCampaignName] = useState('')
  const [basePrompt, setBasePrompt] = useState('')
  const [selectedTargetGroups, setSelectedTargetGroups] = useState<string[]>([])
  const [maxIterations, setMaxIterations] = useState('2')

  // Load target groups from localStorage
  useEffect(() => {
    const savedTargetGroups = localStorage.getItem(STORAGE_KEYS.TARGET_GROUPS)
    if (savedTargetGroups) {
      setTargetGroups(JSON.parse(savedTargetGroups))
    }
  }, [])

  const toggleTargetGroup = (id: string) => {
    setSelectedTargetGroups(prev =>
      prev.includes(id)
        ? prev.filter(groupId => groupId !== id)
        : [...prev, id]
    )
  }

  const handleCreateCampaign = () => {
    if (!campaignName.trim() || !basePrompt.trim() || selectedTargetGroups.length === 0) {
      return
    }

    const newCampaign: Campaign = {
      id: Date.now().toString(),
      name: campaignName.trim(),
      basePrompt: basePrompt.trim(),
      targetGroupIds: selectedTargetGroups,
      maxIterations: parseInt(maxIterations),
      createdAt: new Date().toISOString(),
    }

    // Load existing campaigns
    const savedCampaigns = localStorage.getItem(STORAGE_KEYS.CAMPAIGNS)
    const campaigns: Campaign[] = savedCampaigns
      ? JSON.parse(savedCampaigns)
      : []

    // Add new campaign
    const updatedCampaigns = [...campaigns, newCampaign]
    localStorage.setItem(
      STORAGE_KEYS.CAMPAIGNS,
      JSON.stringify(updatedCampaigns)
    )

    // Navigate back to campaigns list
    navigate({ to: '/campaigns' })
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
        <div>
          <h1 className="text-3xl font-bold">Create New Campaign</h1>
          <p className="text-muted-foreground mt-2">
            Set up a new adaptive image generation campaign
          </p>
        </div>
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
            <Button onClick={handleCreateCampaign}>Create Campaign</Button>
          </div>
        </div>
      </div>
    </div>
  )
}
