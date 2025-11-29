export interface GeneratedImage extends Record<string, unknown> {
  id: string
  imageUrl: string
  isWinner: boolean
  analytics: {
    clickRate: number
    conversionRate: number
    engagement: number
    impressions: number
  }
}

export interface Iteration extends Record<string, unknown> {
  iterationNumber: number
  promptGen: {
    prompt: string
    usedAssets: string[]
    notes?: string
  }
  imageGen: {
    generatedImages: GeneratedImage[]
  }
  analytics: {
    winnerImages: string[]
    differentiationText: string
    differentiationTags: string[]
    improvements: {
      clickRate: string
      conversionRate: string
      engagement: string
    }
  }
}

export interface TargetGroupFlow extends Record<string, unknown> {
  id: string
  name: string
  iterations: Iteration[]
}

export interface FlowData {
  campaignId: string
  campaignName: string
  basePrompt: string
  enhancedPrompt: string
  targetGroups: TargetGroupFlow[]
}

export const getMockFlowData = (campaignId: string): FlowData => {
  return {
    campaignId,
    campaignName: 'Running Shoes Launch',
    basePrompt: 'Create an engaging advertisement for premium running shoes',
    enhancedPrompt:
      'Create a vibrant, high-energy advertisement showcasing premium running shoes with dynamic motion blur, featuring athletic models in urban settings during golden hour',
    targetGroups: [
      {
        id: 'tg-1',
        name: 'Berlin - Young Professionals',
        iterations: [
          {
            iterationNumber: 0,
            promptGen: {
              prompt:
                'Create a vibrant, high-energy advertisement for premium running shoes targeting urban young professionals in Berlin, featuring sleek city backgrounds, modern aesthetics, and lifestyle integration',
              usedAssets: ['Background: Berlin Skyline', 'Product: Running Shoe Pro', 'Model: Athletic Young Professional'],
              notes: 'Initial prompt based on target group demographics',
            },
            imageGen: {
              generatedImages: [
                {
                  id: 'img-1-0',
                  imageUrl: '/mock-images/image-1.jpg',
                  isWinner: true,
                  analytics: {
                    clickRate: 4.8,
                    conversionRate: 2.3,
                    engagement: 87,
                    impressions: 12500,
                  },
                },
                {
                  id: 'img-2-0',
                  imageUrl: '/mock-images/image-2.jpg',
                  isWinner: false,
                  analytics: {
                    clickRate: 3.2,
                    conversionRate: 1.5,
                    engagement: 62,
                    impressions: 11200,
                  },
                },
                {
                  id: 'img-3-0',
                  imageUrl: '/mock-images/image-3.jpg',
                  isWinner: true,
                  analytics: {
                    clickRate: 5.1,
                    conversionRate: 2.7,
                    engagement: 91,
                    impressions: 13800,
                  },
                },
                {
                  id: 'img-4-0',
                  imageUrl: '/mock-images/image-4.jpg',
                  isWinner: false,
                  analytics: {
                    clickRate: 2.9,
                    conversionRate: 1.2,
                    engagement: 58,
                    impressions: 10500,
                  },
                },
                {
                  id: 'img-5-0',
                  imageUrl: '/mock-images/image-5.jpg',
                  isWinner: false,
                  analytics: {
                    clickRate: 3.5,
                    conversionRate: 1.6,
                    engagement: 65,
                    impressions: 11800,
                  },
                },
              ],
            },
            analytics: {
              winnerImages: ['img-1-0', 'img-3-0'],
              differentiationText:
                'Winner images feature warm lighting, visible motion blur on shoes, and prominent Berlin landmarks. Urban context and dynamic poses drive higher engagement.',
              differentiationTags: ['warm-lighting', 'motion-blur', 'urban-landmarks', 'dynamic-pose'],
              improvements: {
                clickRate: '4.95%',
                conversionRate: '2.50%',
                engagement: '89%',
              },
            },
          },
          {
            iterationNumber: 1,
            promptGen: {
              prompt:
                'Premium running shoes ad for Berlin young professionals with warm golden hour lighting, motion blur effect on shoes, prominent Berlin landmarks (TV Tower, Brandenburg Gate), dynamic running poses, urban lifestyle integration',
              usedAssets: ['Background: Berlin TV Tower', 'Background: Brandenburg Gate', 'Product: Running Shoe Pro', 'Model: Athletic Young Professional'],
              notes: 'Refined based on iteration 0 analytics: emphasized warm lighting, motion blur, and specific Berlin landmarks',
            },
            imageGen: {
              generatedImages: [
                {
                  id: 'img-1-1',
                  imageUrl: '/mock-images/image-1.jpg',
                  isWinner: true,
                  analytics: {
                    clickRate: 6.2,
                    conversionRate: 3.1,
                    engagement: 94,
                    impressions: 14200,
                  },
                },
                {
                  id: 'img-2-1',
                  imageUrl: '/mock-images/image-2.jpg',
                  isWinner: true,
                  analytics: {
                    clickRate: 5.9,
                    conversionRate: 2.9,
                    engagement: 92,
                    impressions: 13900,
                  },
                },
                {
                  id: 'img-3-1',
                  imageUrl: '/mock-images/image-3.jpg',
                  isWinner: false,
                  analytics: {
                    clickRate: 4.1,
                    conversionRate: 1.9,
                    engagement: 73,
                    impressions: 12100,
                  },
                },
                {
                  id: 'img-4-1',
                  imageUrl: '/mock-images/image-4.jpg',
                  isWinner: false,
                  analytics: {
                    clickRate: 4.5,
                    conversionRate: 2.0,
                    engagement: 78,
                    impressions: 12800,
                  },
                },
                {
                  id: 'img-5-1',
                  imageUrl: '/mock-images/image-5.jpg',
                  isWinner: false,
                  analytics: {
                    clickRate: 4.4,
                    conversionRate: 2.0,
                    engagement: 76,
                    impressions: 12600,
                  },
                },
              ],
            },
            analytics: {
              winnerImages: ['img-1-1', 'img-2-1'],
              differentiationText:
                'Iteration 1 shows significant improvement. Images with TV Tower in background and strong motion blur effects perform 35% better. Golden hour lighting crucial for engagement.',
              differentiationTags: ['tv-tower', 'strong-motion-blur', 'golden-hour', 'running-action'],
              improvements: {
                clickRate: '6.05% (+22%)',
                conversionRate: '3.00% (+20%)',
                engagement: '93% (+4%)',
              },
            },
          },
        ],
      },
      {
        id: 'tg-2',
        name: 'Munich - Families',
        iterations: [
          {
            iterationNumber: 0,
            promptGen: {
              prompt:
                'Create a warm, family-friendly advertisement for premium running shoes targeting families in Munich, featuring park settings, family activities, and emphasis on comfort and quality',
              usedAssets: ['Background: Munich Park', 'Product: Running Shoe Pro', 'Model: Family Active'],
              notes: 'Initial prompt focused on family values and comfort',
            },
            imageGen: {
              generatedImages: [
                {
                  id: 'img-6-0',
                  imageUrl: '/mock-images/image-1.jpg',
                  isWinner: false,
                  analytics: {
                    clickRate: 3.1,
                    conversionRate: 1.4,
                    engagement: 61,
                    impressions: 10800,
                  },
                },
                {
                  id: 'img-7-0',
                  imageUrl: '/mock-images/image-2.jpg',
                  isWinner: true,
                  analytics: {
                    clickRate: 4.6,
                    conversionRate: 2.1,
                    engagement: 83,
                    impressions: 12100,
                  },
                },
                {
                  id: 'img-8-0',
                  imageUrl: '/mock-images/image-3.jpg',
                  isWinner: false,
                  analytics: {
                    clickRate: 2.8,
                    conversionRate: 1.1,
                    engagement: 56,
                    impressions: 9900,
                  },
                },
                {
                  id: 'img-9-0',
                  imageUrl: '/mock-images/image-4.jpg',
                  isWinner: true,
                  analytics: {
                    clickRate: 4.9,
                    conversionRate: 2.4,
                    engagement: 88,
                    impressions: 13200,
                  },
                },
                {
                  id: 'img-10-0',
                  imageUrl: '/mock-images/image-5.jpg',
                  isWinner: false,
                  analytics: {
                    clickRate: 3.3,
                    conversionRate: 1.5,
                    engagement: 63,
                    impressions: 11000,
                  },
                },
              ],
            },
            analytics: {
              winnerImages: ['img-7-0', 'img-9-0'],
              differentiationText:
                'Winner images show multi-generational families together, English Garden backdrop, soft natural lighting. Family togetherness and Munich-specific locations resonate.',
              differentiationTags: ['multi-generational', 'english-garden', 'natural-lighting', 'family-togetherness'],
              improvements: {
                clickRate: '4.75%',
                conversionRate: '2.25%',
                engagement: '86%',
              },
            },
          },
        ],
      },
    ],
  }
}
