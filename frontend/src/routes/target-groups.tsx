import { createFileRoute } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Plus, Pencil, Trash2 } from 'lucide-react'
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
import { Textarea } from '@/components/ui/textarea'

export const Route = createFileRoute('/target-groups')({
  component: TargetGroups,
})

interface TargetGroup {
  id: string
  name: string
  city: string
  ageGroup: string
  economicStatus: string
  description?: string
}

const STORAGE_KEY = 'adaptive-gen-target-groups'

const GERMAN_CITIES = [
  'Berlin',
  'Hamburg',
  'Munich',
  'Cologne',
  'Frankfurt',
  'Stuttgart',
  'Düsseldorf',
  'Dortmund',
  'Essen',
  'Leipzig',
  'Bremen',
  'Dresden',
  'Hanover',
  'Nuremberg',
]

const AGE_GROUPS = [
  '18-24',
  '25-34',
  '35-44',
  '45-54',
  '55-64',
  '65+',
]

const ECONOMIC_STATUS_OPTIONS = [
  'Low income',
  'Mid income',
  'High income',
  'Very high income',
]

function TargetGroups() {
  const [targetGroups, setTargetGroups] = useState<TargetGroup[]>([])
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingGroup, setEditingGroup] = useState<TargetGroup | null>(null)

  // Form state
  const [name, setName] = useState('')
  const [city, setCity] = useState('')
  const [ageGroup, setAgeGroup] = useState('')
  const [economicStatus, setEconomicStatus] = useState('')
  const [description, setDescription] = useState('')

  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      setTargetGroups(JSON.parse(saved))
    } else {
      // Initialize with default target groups
      const defaultGroups: TargetGroup[] = [
        {
          id: '1',
          name: 'Berlin - Young Professionals',
          city: 'Berlin',
          ageGroup: '',
          economicStatus: '',
          description: 'Urban young professionals in Berlin',
        },
        {
          id: '2',
          name: 'Munich - Families',
          city: 'Munich',
          ageGroup: '',
          economicStatus: '',
          description: 'Families with children in Munich area',
        },
      ]
      setTargetGroups(defaultGroups)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(defaultGroups))
    }
  }, [])

  const resetForm = () => {
    setName('')
    setCity('')
    setAgeGroup('')
    setEconomicStatus('')
    setDescription('')
    setEditingGroup(null)
  }

  const handleOpenDialog = (group?: TargetGroup) => {
    if (group) {
      setEditingGroup(group)
      setName(group.name)
      setCity(group.city)
      setAgeGroup(group.ageGroup)
      setEconomicStatus(group.economicStatus)
      setDescription(group.description || '')
    } else {
      resetForm()
    }
    setDialogOpen(true)
  }

  const handleSave = () => {
    if (!name.trim() || !city) {
      return
    }

    let updatedGroups: TargetGroup[]

    if (editingGroup) {
      // Update existing group
      updatedGroups = targetGroups.map((g) =>
        g.id === editingGroup.id
          ? {
              ...g,
              name: name.trim(),
              city,
              ageGroup,
              economicStatus,
              description: description.trim() || undefined,
            }
          : g
      )
    } else {
      // Create new group
      const newGroup: TargetGroup = {
        id: Date.now().toString(),
        name: name.trim(),
        city,
        ageGroup,
        economicStatus,
        description: description.trim() || undefined,
      }
      updatedGroups = [...targetGroups, newGroup]
    }

    setTargetGroups(updatedGroups)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedGroups))
    setDialogOpen(false)
    resetForm()
  }

  const handleDelete = (id: string) => {
    const updatedGroups = targetGroups.filter((g) => g.id !== id)
    setTargetGroups(updatedGroups)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedGroups))
  }

  return (
    <div className="max-w-screen-lg mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Target Groups</h1>
          <p className="text-muted-foreground mt-2">
            Manage target audience segments for your campaigns
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => handleOpenDialog()}>
              <Plus className="h-4 w-4 mr-2" />
              New Target Group
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>
                {editingGroup ? 'Edit Target Group' : 'Create New Target Group'}
              </DialogTitle>
              <DialogDescription>
                Define a target audience segment for your campaigns
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  placeholder="e.g., Berlin - Young Professionals"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="city">City</Label>
                <Select value={city} onValueChange={setCity}>
                  <SelectTrigger id="city">
                    <SelectValue placeholder="Select a city" />
                  </SelectTrigger>
                  <SelectContent>
                    {GERMAN_CITIES.map((cityName) => (
                      <SelectItem key={cityName} value={cityName}>
                        {cityName}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="ageGroup">Age Group</Label>
                <Select value={ageGroup} onValueChange={setAgeGroup} disabled>
                  <SelectTrigger id="ageGroup">
                    <SelectValue placeholder="Select age group" />
                  </SelectTrigger>
                  <SelectContent>
                    {AGE_GROUPS.map((group) => (
                      <SelectItem key={group} value={group}>
                        {group}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="economicStatus">Economic Status</Label>
                <Select value={economicStatus} onValueChange={setEconomicStatus} disabled>
                  <SelectTrigger id="economicStatus">
                    <SelectValue placeholder="Select economic status" />
                  </SelectTrigger>
                  <SelectContent>
                    {ECONOMIC_STATUS_OPTIONS.map((status) => (
                      <SelectItem key={status} value={status}>
                        {status}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Describe the target audience..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleSave}>
                {editingGroup ? 'Save Changes' : 'Create Target Group'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {targetGroups.length === 0 ? (
        <div className="rounded-lg border bg-card p-12">
          <div className="text-center text-muted-foreground">
            <p className="text-lg mb-2">No target groups yet</p>
            <p className="text-sm">
              Create your first target group to use in campaigns
            </p>
          </div>
        </div>
      ) : (
        <div className="grid gap-4">
          {targetGroups.map((group) => (
            <div
              key={group.id}
              className="rounded-lg border bg-card p-6 hover:border-primary/50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-xl font-semibold mb-2">{group.name}</h3>
                  {group.description && (
                    <p className="text-sm text-muted-foreground mb-4">
                      {group.description}
                    </p>
                  )}
                  <div className="flex gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">City: </span>
                      <span className="font-medium">{group.city}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Age: </span>
                      <span className="font-medium">{group.ageGroup || 'Any'}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">
                        Economic Status:{' '}
                      </span>
                      <span className="font-medium">{group.economicStatus || 'Any'}</span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleOpenDialog(group)}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(group.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
