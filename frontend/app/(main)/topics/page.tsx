import { FeedView } from "@/components/feed/feed-view"
import { listTopics } from "@/lib/repositories/topics"

export default async function TopicsPage() {
  const topics = await listTopics()

  return <FeedView topics={topics} />
}
