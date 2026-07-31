/**
 * Database types for Guild Board.
 *
 * Hand-maintained to mirror `supabase/migrations/`. Once the project is linked
 * you can regenerate the canonical version with `npm run db:types`; keep this
 * file as the source of truth for the enums and view/RPC shapes either way.
 */

export type UserRole = 'requester' | 'member' | 'admin';
export type TaskStatus =
  | 'open'
  | 'assigned'
  | 'in_escrow'
  | 'completed'
  | 'disputed'
  | 'cancelled';
export type RiskTier = 'low' | 'medium' | 'high_licensed';
export type BidStatus = 'pending' | 'accepted' | 'rejected';
export type EscrowStatus = 'pending_hold' | 'held' | 'released' | 'refunded';
export type DisputeStatus =
  | 'open'
  | 'under_review'
  | 'resolved_requester'
  | 'resolved_member';

export type City = {
  id: string;
  name: string;
  slug: string;
  country: string;
  lat: number;
  long: number;
  radius_miles: number;
  timezone: string;
  currency: string;
  active_status: boolean;
  created_at: string;
}

export type Category = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  icon: string | null;
  is_licensed_trade_required: boolean;
  default_risk_tier: RiskTier;
  sort_order: number;
  created_at: string;
}

export type User = {
  id: string;
  full_name: string | null;
  avatar_url: string | null;
  bio: string | null;
  city_id: string | null;
  role: UserRole;
  rep_score: number;
  rep_count: number;
  tasks_completed: number;
  stripe_account_id: string | null;
  stripe_payouts_enabled: boolean;
  stripe_charges_enabled: boolean;
  is_id_verified: boolean;
  id_verified_at: string | null;
  is_background_checked: boolean;
  licensed_trades: string[];
  is_suspended: boolean;
  created_at: string;
  updated_at: string;
}

export type Task = {
  id: string;
  requester_id: string;
  city_id: string;
  category_id: string;
  assigned_to: string | null;
  title: string;
  description: string;
  reward_amount: number;
  currency: string;
  lat: number;
  long: number;
  address_line: string | null;
  status: TaskStatus;
  risk_tier: RiskTier;
  flagged_terms: string[];
  requires_admin_review: boolean;
  image_urls: string[];
  deadline_at: string | null;
  safety_ack_at: string | null;
  safety_ack_version: string | null;
  completed_at: string | null;
  released_after: string | null;
  cancelled_at: string | null;
  created_at: string;
  updated_at: string;
}

export type Bid = {
  id: string;
  task_id: string;
  member_id: string;
  amount: number;
  proposal_text: string;
  estimated_hours: number | null;
  can_start_at: string | null;
  status: BidStatus;
  created_at: string;
  updated_at: string;
}

export type Transaction = {
  id: string;
  task_id: string;
  bid_id: string | null;
  payer_id: string;
  payee_id: string;
  stripe_payment_intent_id: string | null;
  stripe_charge_id: string | null;
  stripe_transfer_id: string | null;
  stripe_destination_account: string | null;
  amount: number;
  platform_fee: number;
  payout_amount: number;
  currency: string;
  escrow_status: EscrowStatus;
  authorized_at: string | null;
  held_at: string | null;
  released_at: string | null;
  refunded_at: string | null;
  release_reason: string | null;
  failure_code: string | null;
  created_at: string;
  updated_at: string;
}

export type Dispute = {
  id: string;
  task_id: string;
  raised_by: string;
  reason: string;
  evidence_urls: string[];
  resolution_notes: string | null;
  resolved_by: string | null;
  status: DisputeStatus;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

export type Review = {
  id: string;
  task_id: string;
  reviewer_id: string;
  reviewee_id: string;
  rating: number;
  comment: string | null;
  created_at: string;
}

export type Message = {
  id: string;
  task_id: string;
  sender_id: string;
  body: string | null;
  attachment_urls: string[];
  is_proof: boolean;
  read_at: string | null;
  created_at: string;
}

/** Row shape returned by the `tasks_within_radius` RPC. */
export type TaskWithDistance = {
  id: string;
  title: string;
  description: string;
  reward_amount: number;
  lat: number;
  long: number;
  status: TaskStatus;
  risk_tier: RiskTier;
  category_id: string;
  requester_id: string;
  image_urls: string[];
  deadline_at: string | null;
  created_at: string;
  distance_miles: number;
  bid_count: number;
}

export type EscrowAutoReleaseRow = {
  transaction_id: string;
  task_id: string;
  stripe_payment_intent_id: string | null;
  amount: number;
  platform_fee: number;
  payout_amount: number;
  currency: string;
  stripe_destination_account: string | null;
  released_after: string;
  hours_overdue: number;
}

type Insertable<T, Required extends keyof T, Optional extends keyof T> = Pick<
  T,
  Required
> &
  Partial<Pick<T, Optional>>;

/**
 * Relationship metadata mirrors the foreign keys in 001_initial_schema.sql.
 * postgrest-js uses it to resolve `!constraint_name` join hints, so the names
 * here must match the constraint names Postgres actually generated.
 */
type Rel<
  Name extends string,
  Column extends string,
  Referenced extends string,
> = {
  foreignKeyName: Name;
  columns: [Column];
  isOneToOne: false;
  referencedRelation: Referenced;
  referencedColumns: ['id'];
};

export interface Database {
  public: {
    Tables: {
      cities: {
        Row: City;
        Insert: Insertable<City, 'name' | 'slug' | 'country' | 'lat' | 'long', keyof City>;
        Update: Partial<City>;
        Relationships: [];
      };
      categories: {
        Row: Category;
        Insert: Insertable<Category, 'name' | 'slug', keyof Category>;
        Update: Partial<Category>;
        Relationships: [];
      };
      users: {
        Row: User;
        Insert: Insertable<User, 'id', keyof User>;
        Update: Partial<User>;
        Relationships: [Rel<'users_city_id_fkey', 'city_id', 'cities'>];
      };
      tasks: {
        Row: Task;
        Insert: Insertable<
          Task,
          | 'requester_id'
          | 'city_id'
          | 'category_id'
          | 'title'
          | 'description'
          | 'reward_amount'
          | 'lat'
          | 'long',
          keyof Task
        >;
        Update: Partial<Task>;
        Relationships: [
          Rel<'tasks_requester_id_fkey', 'requester_id', 'users'>,
          Rel<'tasks_assigned_to_fkey', 'assigned_to', 'users'>,
          Rel<'tasks_city_id_fkey', 'city_id', 'cities'>,
          Rel<'tasks_category_id_fkey', 'category_id', 'categories'>,
        ];
      };
      bids: {
        Row: Bid;
        Insert: Insertable<
          Bid,
          'task_id' | 'member_id' | 'amount' | 'proposal_text',
          keyof Bid
        >;
        Update: Partial<Bid>;
        Relationships: [
          Rel<'bids_task_id_fkey', 'task_id', 'tasks'>,
          Rel<'bids_member_id_fkey', 'member_id', 'users'>,
        ];
      };
      transactions: {
        Row: Transaction;
        Insert: Insertable<
          Transaction,
          'task_id' | 'payer_id' | 'payee_id' | 'amount',
          keyof Transaction
        >;
        Update: Partial<Transaction>;
        Relationships: [
          Rel<'transactions_task_id_fkey', 'task_id', 'tasks'>,
          Rel<'transactions_bid_id_fkey', 'bid_id', 'bids'>,
          Rel<'transactions_payer_id_fkey', 'payer_id', 'users'>,
          Rel<'transactions_payee_id_fkey', 'payee_id', 'users'>,
        ];
      };
      disputes: {
        Row: Dispute;
        Insert: Insertable<Dispute, 'task_id' | 'raised_by' | 'reason', keyof Dispute>;
        Update: Partial<Dispute>;
        Relationships: [
          Rel<'disputes_task_id_fkey', 'task_id', 'tasks'>,
          Rel<'disputes_raised_by_fkey', 'raised_by', 'users'>,
        ];
      };
      reviews: {
        Row: Review;
        Insert: Insertable<
          Review,
          'task_id' | 'reviewer_id' | 'reviewee_id' | 'rating',
          keyof Review
        >;
        Update: Partial<Review>;
        Relationships: [
          Rel<'reviews_task_id_fkey', 'task_id', 'tasks'>,
          Rel<'reviews_reviewer_id_fkey', 'reviewer_id', 'users'>,
          Rel<'reviews_reviewee_id_fkey', 'reviewee_id', 'users'>,
        ];
      };
      messages: {
        Row: Message;
        Insert: Insertable<Message, 'task_id' | 'sender_id', keyof Message>;
        Update: Partial<Message>;
        Relationships: [
          Rel<'messages_task_id_fkey', 'task_id', 'tasks'>,
          Rel<'messages_sender_id_fkey', 'sender_id', 'users'>,
        ];
      };
    };
    Views: {
      escrow_auto_release_queue: {
        Row: EscrowAutoReleaseRow;
        Relationships: [];
      };
    };
    Functions: {
      tasks_within_radius: {
        Args: {
          p_city_slug: string;
          p_lat: number;
          p_long: number;
          p_radius_miles?: number;
          p_category_ids?: string[] | null;
          p_min_reward?: number | null;
          p_max_reward?: number | null;
          p_limit?: number;
          p_offset?: number;
        };
        Returns: TaskWithDistance[];
      };
      sign_off_task: {
        Args: { p_task_id: string; p_hold_hours?: number };
        Returns: Task;
      };
      mark_task_delivered: {
        Args: { p_task_id: string; p_auto_release_hours?: number };
        Returns: Task;
      };
      resolve_dispute: {
        Args: { p_dispute_id: string; p_status: DisputeStatus; p_notes: string };
        Returns: {
          dispute_id: string;
          task_id: string;
          payment_intent_id: string | null;
          action: 'refund' | 'capture' | 'none';
        }[];
      };
      is_admin: { Args: { uid?: string }; Returns: boolean };
      is_task_participant: { Args: { tid: string; uid?: string }; Returns: boolean };
      is_task_owner: { Args: { tid: string; uid?: string }; Returns: boolean };
    };
    Enums: {
      user_role: UserRole;
      task_status: TaskStatus;
      risk_tier: RiskTier;
      bid_status: BidStatus;
      escrow_status: EscrowStatus;
      dispute_status: DisputeStatus;
    };
    CompositeTypes: Record<string, never>;
  };
}

/** Joined shapes the UI actually renders. */
export type TaskWithRelations = Task & {
  category: Pick<Category, 'id' | 'name' | 'slug' | 'icon' | 'is_licensed_trade_required'>;
  city: Pick<City, 'id' | 'name' | 'slug' | 'currency'>;
  requester: Pick<User, 'id' | 'full_name' | 'avatar_url' | 'rep_score' | 'rep_count' | 'is_id_verified'>;
  bid_count?: number;
  distance_miles?: number;
};

export type BidWithMember = Bid & {
  member: Pick<
    User,
    | 'id'
    | 'full_name'
    | 'avatar_url'
    | 'rep_score'
    | 'rep_count'
    | 'tasks_completed'
    | 'is_id_verified'
    | 'is_background_checked'
    | 'licensed_trades'
  >;
};

export type MessageWithSender = Message & {
  sender: Pick<User, 'id' | 'full_name' | 'avatar_url'>;
};
