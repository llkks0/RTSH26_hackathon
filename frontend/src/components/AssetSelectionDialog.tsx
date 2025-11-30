import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Check } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { useAssets } from '@/lib/api/hooks/useAssets'
import { apiClient } from '@/lib/api/client'

interface AssetSelectionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  selectedAssetIds: string[]
  onSave: (assetIds: string[]) => void
}

export function AssetSelectionDialog({
  open,
  onOpenChange,
  selectedAssetIds,
  onSave,
}: AssetSelectionDialogProps) {
  const { data: assets = [], isLoading } = useAssets()
  const [selected, setSelected] = useState<string[]>(selectedAssetIds)

  // Reset selection when dialog opens
  useEffect(() => {
    if (open) {
      setSelected(selectedAssetIds)
    }
  }, [open, selectedAssetIds])

  const toggleAsset = (assetId: string) => {
    setSelected(prev =>
      prev.includes(assetId)
        ? prev.filter(id => id !== assetId)
        : [...prev, assetId]
    )
  }

  const handleSave = () => {
    onSave(selected)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px] max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Select Assets</DialogTitle>
          <DialogDescription>
            Choose the assets to include in this campaign ({selected.length} selected)
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto py-4">
          {isLoading ? (
            <p className="text-center text-muted-foreground">Loading assets...</p>
          ) : assets.length === 0 ? (
            <p className="text-center text-muted-foreground">
              No assets available. Upload some assets first.
            </p>
          ) : (
            <div className="grid grid-cols-3 md:grid-cols-4 gap-3">
              {assets.map((asset) => {
                const isSelected = selected.includes(asset.id)
                return (
                  <div
                    key={asset.id}
                    className={`relative rounded-lg border-2 overflow-hidden cursor-pointer transition-all ${
                      isSelected
                        ? 'border-primary ring-2 ring-primary/20'
                        : 'border-border hover:border-primary/50'
                    }`}
                    onClick={() => toggleAsset(asset.id)}
                  >
                    <div className="aspect-square overflow-hidden bg-muted flex items-center justify-center">
                      <img
                        src={apiClient.getAssetFileUrl(asset.file_name)}
                        alt={asset.name}
                        className="max-h-full max-w-full object-contain"
                      />
                    </div>
                    <div className="p-2 border-t">
                      <p className="text-xs font-medium truncate">{asset.name}</p>
                      <p className="text-xs text-muted-foreground">{asset.asset_type}</p>
                    </div>
                    {isSelected && (
                      <div className="absolute top-2 right-2 h-6 w-6 rounded-full bg-primary flex items-center justify-center">
                        <Check className="h-4 w-4 text-primary-foreground" />
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save Selection ({selected.length})
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
