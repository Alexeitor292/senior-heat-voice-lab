import { notFound } from "next/navigation";
import { AppShell } from "@/components/shell/AppShell";
import { CheckInReviewView } from "@/components/views/CheckInReviewView";
import { getCheckInReview } from "@/lib/api";

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props) {
  const { id } = await params;
  const review = await getCheckInReview(id);

  return {
    title: review
      ? `Check-In #${review.check_in.id} – Senior Heat Voice Lab`
      : "Check-In Not Found",
  };
}

export default async function CheckInReviewPage({ params }: Props) {
  const { id } = await params;
  const review = await getCheckInReview(id);

  if (!review) notFound();

  return (
    <AppShell>
      <CheckInReviewView review={review} />
    </AppShell>
  );
}