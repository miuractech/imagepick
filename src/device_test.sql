create table public.device_test (
  id uuid not null default gen_random_uuid (),
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  folder_name text not null,
  images text[] null default '{}'::text[],
  device_id uuid null,
  device_name text null,
  device_type text null,
  test_results jsonb null,
  test_date timestamp with time zone null,
  test_status text null,
  upload_batch text null,
  notes text null,
  metadata jsonb null default '{}'::jsonb,
  data jsonb null,
  data_type text null,
  constraint device_test_pkey primary key (id),
  constraint unique_folder_device unique (folder_name, device_id),
  constraint device_test_device_id_fkey foreign KEY (device_id) references devices (id),
  constraint device_test_test_status_check check (
    (
      test_status = any (
        array[
          'pending'::text,
          'passed'::text,
          'failed'::text,
          'incomplete'::text
        ]
      )
    )
  )
) TABLESPACE pg_default;

create index IF not exists idx_device_test_data on public.device_test using gin (data) TABLESPACE pg_default;

create index IF not exists idx_device_test_data_type on public.device_test using btree (data_type) TABLESPACE pg_default;

create index IF not exists idx_device_test_device_id on public.device_test using btree (device_id) TABLESPACE pg_default;

create index IF not exists idx_device_test_folder_name on public.device_test using btree (folder_name) TABLESPACE pg_default;

create index IF not exists idx_device_test_metadata on public.device_test using gin (metadata) TABLESPACE pg_default;

create index IF not exists idx_device_test_results on public.device_test using gin (test_results) TABLESPACE pg_default;

create index IF not exists idx_device_test_status on public.device_test using btree (test_status) TABLESPACE pg_default;

create index IF not exists idx_device_test_test_date on public.device_test using btree (test_date) TABLESPACE pg_default;

create trigger update_device_test_updated_at BEFORE
update on device_test for EACH row
execute FUNCTION update_updated_at_column ();