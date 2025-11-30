import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import type { CampaignFull } from '@/lib/api/types'

interface CampaignSpecDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  campaign: CampaignFull | null
}

export function CampaignSpecDialog({ open, onOpenChange, campaign }: CampaignSpecDialogProps) {
  const spec = campaign?.campaign_spec

  if (!spec) {
    return null
  }

  // Get target group names from the flows
  const targetGroupNames = campaign.campaign_flows
    .map(flow => flow.target_group?.name)
    .filter(Boolean)
    .join(', ')

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Campaign Specification</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-muted-foreground text-xs uppercase tracking-wide">
              Campaign Name
            </Label>
            <p className="text-sm font-medium">{spec.name}</p>
          </div>

          <div className="space-y-1.5">
            <Label className="text-muted-foreground text-xs uppercase tracking-wide">
              Base Prompt
            </Label>
            <p className="text-sm bg-muted p-3 rounded-md whitespace-pre-wrap">
              {spec.base_prompt}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label className="text-muted-foreground text-xs uppercase tracking-wide">
                Max Iterations
              </Label>
              <p className="text-sm font-medium">{spec.max_iterations}</p>
            </div>
            <div className="space-y-1.5">
              <Label className="text-muted-foreground text-xs uppercase tracking-wide">
                Created
              </Label>
              <p className="text-sm font-medium">
                {new Date(spec.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>

          {targetGroupNames && (
            <div className="space-y-1.5">
              <Label className="text-muted-foreground text-xs uppercase tracking-wide">
                Target Groups
              </Label>
              <p className="text-sm font-medium">{targetGroupNames}</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
