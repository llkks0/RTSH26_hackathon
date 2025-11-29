import { createFileRoute } from '@tanstack/react-router'
import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Plus, Settings, Pencil, Trash2, Upload } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
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

export const Route = createFileRoute('/assets')({
  component: Assets,
})

interface AssetType {
  id: string
  label: string
}

interface Asset {
  id: string
  name: string
  fileName: string
  fileUrl: string // base64 data URL for localStorage persistence
  assetTypeId: string
}

const STORAGE_KEYS = {
  ASSETS: 'adaptive-gen-assets',
  ASSET_TYPES: 'adaptive-gen-asset-types',
}

function Assets() {
  const [assetTypes, setAssetTypes] = useState<AssetType[]>([])
  const [assets, setAssets] = useState<Asset[]>([])
  const [newTypeLabel, setNewTypeLabel] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingLabel, setEditingLabel] = useState('')
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null)
  const [assetDialogOpen, setAssetDialogOpen] = useState(false)
  const [renameValue, setRenameValue] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // New asset upload dialog state
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [pendingFile, setPendingFile] = useState<File | null>(null)
  const [pendingFileUrl, setPendingFileUrl] = useState<string>('')
  const [newAssetName, setNewAssetName] = useState('')
  const [newAssetType, setNewAssetType] = useState('')

  // Load from localStorage on mount
  useEffect(() => {
    const savedAssetTypes = localStorage.getItem(STORAGE_KEYS.ASSET_TYPES)
    const savedAssets = localStorage.getItem(STORAGE_KEYS.ASSETS)

    if (savedAssetTypes) {
      setAssetTypes(JSON.parse(savedAssetTypes))
    } else {
      // Initialize with default asset types
      const defaultTypes: AssetType[] = [
        { id: '1', label: 'background' },
        { id: '2', label: 'product' },
        { id: '3', label: 'model' },
        { id: '4', label: 'logo' },
      ]
      setAssetTypes(defaultTypes)
      localStorage.setItem(STORAGE_KEYS.ASSET_TYPES, JSON.stringify(defaultTypes))
    }

    if (savedAssets) {
      setAssets(JSON.parse(savedAssets))
    }
  }, [])

  // Save asset types to localStorage whenever they change
  useEffect(() => {
    if (assetTypes.length > 0) {
      localStorage.setItem(STORAGE_KEYS.ASSET_TYPES, JSON.stringify(assetTypes))
    }
  }, [assetTypes])

  // Save assets to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.ASSETS, JSON.stringify(assets))
  }, [assets])

  const handleAddType = () => {
    if (newTypeLabel.trim()) {
      setAssetTypes([
        ...assetTypes,
        { id: Date.now().toString(), label: newTypeLabel.trim() },
      ])
      setNewTypeLabel('')
    }
  }

  const handleEditType = (id: string) => {
    const type = assetTypes.find((t) => t.id === id)
    if (type) {
      setEditingId(id)
      setEditingLabel(type.label)
    }
  }

  const handleSaveEdit = () => {
    if (editingId && editingLabel.trim()) {
      setAssetTypes(
        assetTypes.map((t) =>
          t.id === editingId ? { ...t, label: editingLabel.trim() } : t
        )
      )
      setEditingId(null)
      setEditingLabel('')
    }
  }

  const handleDeleteType = (id: string) => {
    setAssetTypes(assetTypes.filter((t) => t.id !== id))
  }

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

    const file = files[0] // Take first file only
    if (file.type.startsWith('image/')) {
      try {
        const dataUrl = await fileToBase64(file)
        setPendingFile(file)
        setPendingFileUrl(dataUrl)
        setNewAssetName(file.name.replace(/\.[^/.]+$/, '')) // Remove extension
        setNewAssetType('')
        setUploadDialogOpen(true)
      } catch (error) {
        console.error('Error reading file:', error)
      }
    }

    // Clear file input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleSaveNewAsset = () => {
    if (!pendingFile || !newAssetName.trim() || !newAssetType) {
      return
    }

    const asset: Asset = {
      id: Date.now().toString() + Math.random(),
      name: newAssetName.trim(),
      fileName: pendingFile.name,
      fileUrl: pendingFileUrl, // base64 data URL
      assetTypeId: newAssetType,
    }

    setAssets([...assets, asset])

    // Reset dialog state
    setPendingFile(null)
    setPendingFileUrl('')
    setNewAssetName('')
    setNewAssetType('')
    setUploadDialogOpen(false)
  }

  const handleCancelUpload = () => {
    // No need to revoke data URLs, they don't create memory leaks like blob URLs
    setPendingFile(null)
    setPendingFileUrl('')
    setNewAssetName('')
    setNewAssetType('')
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
    setRenameValue(asset.fileName)
    setAssetDialogOpen(true)
  }

  const handleRenameAsset = () => {
    if (selectedAsset && renameValue.trim()) {
      setAssets(
        assets.map((a) =>
          a.id === selectedAsset.id ? { ...a, fileName: renameValue.trim() } : a
        )
      )
      setAssetDialogOpen(false)
    }
  }

  const handleDeleteAsset = () => {
    if (selectedAsset) {
      setAssets(assets.filter((a) => a.id !== selectedAsset.id))
      setAssetDialogOpen(false)
    }
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
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="outline" size="icon">
                <Settings className="h-4 w-4" />
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Manage Asset Types</DialogTitle>
                <DialogDescription>
                  Create and manage asset type categories for your images
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                {/* Existing Asset Types */}
                <div className="space-y-2">
                  <Label>Current Asset Types</Label>
                  <div className="space-y-2 max-h-[300px] overflow-y-auto">
                    {assetTypes.map((type) => (
                      <div
                        key={type.id}
                        className="flex items-center gap-2 py-3 px-4 rounded-md border bg-background"
                      >
                        {editingId === type.id ? (
                          <>
                            <Input
                              value={editingLabel}
                              onChange={(e) => setEditingLabel(e.target.value)}
                              className="flex-1"
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') handleSaveEdit()
                                if (e.key === 'Escape') {
                                  setEditingId(null)
                                  setEditingLabel('')
                                }
                              }}
                              autoFocus
                            />
                            <Button
                              size="sm"
                              onClick={handleSaveEdit}
                            >
                              Save
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setEditingId(null)
                                setEditingLabel('')
                              }}
                            >
                              Cancel
                            </Button>
                          </>
                        ) : (
                          <>
                            <span className="flex-1">{type.label}</span>
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => handleEditType(type.id)}
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => handleDeleteType(type.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Add New Type */}
                <div className="space-y-2">
                  <Label htmlFor="newType">Add New Asset Type</Label>
                  <div className="flex gap-2">
                    <Input
                      id="newType"
                      placeholder="e.g., background, product, model"
                      value={newTypeLabel}
                      onChange={(e) => setNewTypeLabel(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleAddType()
                      }}
                    />
                    <Button onClick={handleAddType}>
                      <Plus className="h-4 w-4 mr-2" />
                      Add
                    </Button>
                  </div>
                </div>
              </div>
            </DialogContent>
          </Dialog>
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

      {/* Drag and Drop Area / Asset Grid */}
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
                <div className="aspect-square overflow-hidden">
                  <img
                    src={asset.fileUrl}
                    alt={asset.fileName}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="p-3 border-t">
                  <p className="text-sm font-medium truncate">{asset.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {assetTypes.find((t) => t.id === asset.assetTypeId)?.label || 'Unknown'}
                  </p>
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
            {/* Asset Preview */}
            {pendingFileUrl && (
              <div className="rounded-lg border overflow-hidden">
                <img
                  src={pendingFileUrl}
                  alt="Preview"
                  className="w-full h-auto"
                />
              </div>
            )}

            {/* Asset Name */}
            <div className="space-y-2">
              <Label htmlFor="newAssetName">Asset Name</Label>
              <Input
                id="newAssetName"
                placeholder="e.g., Running shoe product shot"
                value={newAssetName}
                onChange={(e) => setNewAssetName(e.target.value)}
              />
            </div>

            {/* Asset Type */}
            <div className="space-y-2">
              <Label htmlFor="assetType">Asset Type</Label>
              <Select value={newAssetType} onValueChange={setNewAssetType}>
                <SelectTrigger id="assetType">
                  <SelectValue placeholder="Select asset type" />
                </SelectTrigger>
                <SelectContent>
                  {assetTypes.map((type) => (
                    <SelectItem key={type.id} value={type.id}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={handleCancelUpload}>
              Cancel
            </Button>
            <Button onClick={handleSaveNewAsset}>
              Save Asset
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
              Rename or delete this asset
            </DialogDescription>
          </DialogHeader>
          {selectedAsset && (
            <div className="space-y-4 py-4">
              {/* Asset Preview */}
              <div className="rounded-lg border overflow-hidden">
                <img
                  src={selectedAsset.fileUrl}
                  alt={selectedAsset.fileName}
                  className="w-full h-auto"
                />
              </div>

              {/* Rename */}
              <div className="space-y-2">
                <Label htmlFor="assetName">Asset Name</Label>
                <Input
                  id="assetName"
                  value={renameValue}
                  onChange={(e) => setRenameValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleRenameAsset()
                  }}
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="destructive" onClick={handleDeleteAsset}>
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </Button>
            <Button onClick={handleRenameAsset}>
              <Pencil className="h-4 w-4 mr-2" />
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
