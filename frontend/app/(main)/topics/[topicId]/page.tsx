import { notFound } from "next/navigation"

import { TopicDetailView } from "@/components/topics/topic-detail-view"
import { getTopicDetail } from "@/lib/repositories/topics"

interface Props {
  params: Promise<{ topicId: string }>
}

export default async function TopicPage({ params }: Props) {
  const { topicId } = await params
  const topic = await getTopicDetail(topicId)

  if (!topic) {
    notFound()
  }

  return <TopicDetailView topic={topic} />
}
