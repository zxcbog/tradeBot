CREATE TABLE IF NOT EXISTS public.markets
(
    market_id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    market_name text NOT NULL,
    CONSTRAINT markets_pkey PRIMARY KEY (market_id)
);

CREATE TABLE IF NOT EXISTS public.transactions
(
    date timestamp with time zone NOT NULL DEFAULT now(),
    transaction_id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    transaction_type text NOT NULL,
    money_amount double precision NOT NULL,
    market_id bigint NOT NULL,
    symbol_amount double precision NOT NULL DEFAULT 0,
    CONSTRAINT "Transactions_pkey" PRIMARY KEY (transaction_id),
    CONSTRAINT market_id FOREIGN KEY (market_id)
        REFERENCES public.markets (market_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
);

CREATE TABLE IF NOT EXISTS public.users
(
    user_id bigint NOT NULL,
    user_money_usdt double precision NOT NULL DEFAULT 0,
    CONSTRAINT users_pkey PRIMARY KEY (user_id)
);
