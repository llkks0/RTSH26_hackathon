import { createFileRoute } from '@tanstack/react-router'
import { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Plus, Pencil, Trash2, Upload } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useAssets, useUploadAsset, useUpdateAsset, useDeleteAsset } from '@/lib/api/hooks/useAssets'
import { apiClient } from '@/lib/api/client'
import type { Asset, AssetType } from '@/lib/api/types'

export const Route = createFileRoute('/assets')({
  component: Assets,
})

const ASSET_TYPES: AssetType[] = [
  'background',
  'product',
  'model',
  'logo',
  'slogan',
  'tagline',
  'headline',
  'description',
  'cta',
]

function Assets() {
  const { data: assets = [], isLoading } = useAssets()
  const uploadAsset = useUploadAsset()
  const updateAsset = useUpdateAsset()
  const deleteAsset = useDeleteAsset()

  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null)
  const [assetDialogOpen, setAssetDialogOpen] = useState(false)
  const [editName, setEditName] = useState('')
  const [editCaption, setEditCaption] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // New asset upload dialog state
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [pendingFile, setPendingFile] = useState<File | null>(null)
  const [pendingFileUrl, setPendingFileUrl] = useState<string>('')
  const [newAssetName, setNewAssetName] = useState('')
  const [newAssetType, setNewAssetType] = useState<AssetType | ''>('')
  const [newAssetCaption, setNewAssetCaption] = useState('')
  const [newAssetTags, setNewAssetTags] = useState('')

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = reject
      reader.readAsDataURL(file)
    })
  }

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return

    const file = files[0]
    if (file.type.startsWith('image/')) {
      try {
        const dataUrl = await fileToBase64(file)
        setPendingFile(file)
        setPendingFileUrl(dataUrl)
        setNewAssetName(file.name.replace(/\.[^/.]+$/, ''))
        setNewAssetType('')
        setNewAssetCaption('')
        setNewAssetTags('')
        setUploadDialogOpen(true)
      } catch (error) {
        console.error('Error reading file:', error)
      }
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleSaveNewAsset = () => {
    if (!pendingFile || !newAssetName.trim() || !newAssetType) {
      return
    }

    // Create FormData for file upload
    const formData = new FormData()
    formData.append('file', pendingFile)
    formData.append('name', newAssetName.trim())
    formData.append('asset_type', newAssetType)
    formData.append('caption', newAssetCaption.trim() || newAssetName.trim())

    // Add tags as comma-separated string
    const tags = newAssetTags.split(',').map(t => t.trim()).filter(Boolean)
    tags.forEach(tag => formData.append('tags', tag))

    uploadAsset.mutate(formData, {
      onSuccess: () => {
        setPendingFile(null)
        setPendingFileUrl('')
        setNewAssetName('')
        setNewAssetType('')
        setNewAssetCaption('')
        setNewAssetTags('')
        setUploadDialogOpen(false)
      }
    })
  }

  const handleCancelUpload = () => {
    setPendingFile(null)
    setPendingFileUrl('')
    setNewAssetName('')
    setNewAssetType('')
    setNewAssetCaption('')
    setNewAssetTags('')
    setUploadDialogOpen(false)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    handleFileUpload(e.dataTransfer.files)
  }

  const handleAssetClick = (asset: Asset) => {
    setSelectedAsset(asset)
    setEditName(asset.name)
    setEditCaption(asset.caption)
    setAssetDialogOpen(true)
  }

  const handleUpdateAsset = () => {
    if (selectedAsset && editName.trim()) {
      updateAsset.mutate({
        assetId: selectedAsset.id,
        data: {
          name: editName.trim(),
          caption: editCaption.trim(),
        }
      }, {
        onSuccess: () => {
          setAssetDialogOpen(false)
        }
      })
    }
  }

  const handleDeleteAsset = () => {
    if (selectedAsset) {
      deleteAsset.mutate(selectedAsset.id, {
        onSuccess: () => {
          setAssetDialogOpen(false)
        }
      })
    }
  }

  if (isLoading) {
    return (
      <div className="max-w-screen-lg mx-auto">
        <p>Loading assets...</p>
      </div>
    )
  }

  return (
    <div className="max-w-screen-lg mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Assets</h1>
          <p className="text-muted-foreground mt-2">
            Manage your image assets for campaign generation
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={() => fileInputRef.current?.click()}>
            <Plus className="h-4 w-4 mr-2" />
            Upload Asset
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => handleFileUpload(e.target.files)}
          />
        </div>
      </div>

      <div
        className={`rounded-lg border-2 border-dashed bg-card p-12 transition-colors ${
          isDragging ? 'border-primary bg-accent' : 'border-border'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {assets.length === 0 ? (
          <div className="text-center text-muted-foreground">
            <Upload className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg mb-2">No assets yet</p>
            <p className="text-sm">
              Drag and drop images here or click "Upload Asset" to get started
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {assets.map((asset) => (
              <div
                key={asset.id}
                className="group relative rounded-lg border bg-background overflow-hidden cursor-pointer hover:border-primary transition-colors"
                onClick={() => handleAssetClick(asset)}
              >
                <div className="aspect-square overflow-hidden bg-muted flex items-center justify-center">
                  <img
                    src={apiClient.getAssetFileUrl(asset.file_name)}
                    alt={asset.name}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="p-3 border-t">
                  <p className="text-sm font-medium truncate">{asset.name}</p>
                  <p className="text-xs text-muted-foreground">{asset.asset_type}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upload Asset Dialog */}
      <Dialog open={uploadDialogOpen} onOpenChange={(open) => !open && handleCancelUpload()}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Add New Asset</DialogTitle>
            <DialogDescription>
              Configure your asset details before saving
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {pendingFileUrl && (
              <div className="rounded-lg border overflow-hidden">
                <img
                  src={pendingFileUrl}
                  alt="Preview"
                  className="w-full h-auto"
                />
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="newAssetName">Asset Name</Label>
              <Input
                id="newAssetName"
                placeholder="e.g., Running shoe product shot"
                value={newAssetName}
                onChange={(e) => setNewAssetName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="assetType">Asset Type</Label>
              <Select value={newAssetType} onValueChange={(value) => setNewAssetType(value as AssetType)}>
                <SelectTrigger id="assetType">
                  <SelectValue placeholder="Select asset type" />
                </SelectTrigger>
                <SelectContent>
                  {ASSET_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="caption">Caption</Label>
              <Textarea
                id="caption"
                placeholder="Describe this asset for AI processing"
                value={newAssetCaption}
                onChange={(e) => setNewAssetCaption(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tags">Tags (comma-separated)</Label>
              <Input
                id="tags"
                placeholder="e.g., red, outdoor, running"
                value={newAssetTags}
                onChange={(e) => setNewAssetTags(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={handleCancelUpload}>
              Cancel
            </Button>
            <Button onClick={handleSaveNewAsset} disabled={uploadAsset.isPending}>
              {uploadAsset.isPending ? 'Uploading...' : 'Save Asset'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Asset Management Dialog */}
      <Dialog open={assetDialogOpen} onOpenChange={setAssetDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Manage Asset</DialogTitle>
            <DialogDescription>
              Update or delete this asset
            </DialogDescription>
          </DialogHeader>
          {selectedAsset && (
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="assetName">Asset Name</Label>
                <Input
                  id="assetName"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="editCaption">Caption</Label>
                <Textarea
                  id="editCaption"
                  value={editCaption}
                  onChange={(e) => setEditCaption(e.target.value)}
                />
              </div>

              <div className="space-y-1 text-sm">
                <p><span className="font-medium">Type:</span> {selectedAsset.asset_type}</p>
                <p><span className="font-medium">File:</span> {selectedAsset.file_name}</p>
                {selectedAsset.tags.length > 0 && (
                  <p><span className="font-medium">Tags:</span> {selectedAsset.tags.join(', ')}</p>
                )}
              </div>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="destructive"
              onClick={handleDeleteAsset}
              disabled={deleteAsset.isPending}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              {deleteAsset.isPending ? 'Deleting...' : 'Delete'}
            </Button>
            <Button
              onClick={handleUpdateAsset}
              disabled={updateAsset.isPending}
            >
              <Pencil className="h-4 w-4 mr-2" />
              {updateAsset.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
