alter table races add column bad_timing tinyint not null default 0;
alter table races add column note varchar(512) not null default '';