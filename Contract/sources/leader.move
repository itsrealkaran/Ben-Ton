module benton::leaderboard {
    use std::signer;
    use std::vector;
    use aptos_std::table::{Self, Table};
    use aptos_framework::object;

    struct LeaderboardEntry has store, drop, copy {
        address: address,
        score: u64,
    }

    struct Leaderboard has key {
        owner: address,
        entries: vector<LeaderboardEntry>,
        scores: Table<address, u64>,
    }

    const MAX_LEADERBOARD_SIZE: u64 = 15;


    public entry fun initialize(account: &signer) {
        let leaderboard_obj = object::create_named_object(
            account,
            b"leaderboard"
        );
        let obj_signer = object::generate_signer(&leaderboard_obj);
        move_to(&obj_signer, Leaderboard {
            owner: signer::address_of(account),
            entries: vector::empty(),
            scores: table::new(),
        });
    }

    public entry fun update_score(player: &signer, score: u64) acquires Leaderboard {
        let player_address = signer::address_of(player);
        let leaderboard_addr = object::create_object_address(&@benton, b"leaderboard");
        let leaderboard = borrow_global_mut<Leaderboard>(leaderboard_addr);
        
        if (table::contains(&leaderboard.scores, player_address)) {
            let old_score = table::remove(&mut leaderboard.scores, player_address);
            remove_entry(&mut leaderboard.entries, player_address);
            if (score > old_score) {
                table::add(&mut leaderboard.scores, player_address, score);
                insert_entry(&mut leaderboard.entries, player_address, score);
            } else {
                table::add(&mut leaderboard.scores, player_address, old_score);
                insert_entry(&mut leaderboard.entries, player_address, old_score);
            }
        } else {
            table::add(&mut leaderboard.scores, player_address, score);
            insert_entry(&mut leaderboard.entries, player_address, score);
        }
    }

    fun insert_entry(entries: &mut vector<LeaderboardEntry>, addr: address, score: u64) {
        let new_entry = LeaderboardEntry { address: addr, score };
        let i = 0;
        let len = vector::length(entries);
        while (i < len && score <= vector::borrow(entries, i).score) {
            i = i + 1;
        };
        vector::push_back(entries, new_entry);
        let j = vector::length(entries) - 1;
        while (j > i) {
            vector::swap(entries, j - 1, j);
            j = j - 1;
        };
        if (vector::length(entries) > MAX_LEADERBOARD_SIZE) {
            vector::pop_back(entries);
        };
    }

    fun remove_entry(entries: &mut vector<LeaderboardEntry>, addr: address) {
        let i = 0;
        let len = vector::length(entries);
        while (i < len) {
            if (vector::borrow(entries, i).address == addr) {
                vector::remove(entries, i);
                break
            };
            i = i + 1;
        };
    }

    #[view]
    public fun get_top_players(): vector<LeaderboardEntry> acquires Leaderboard {
        let leaderboard_addr = object::create_object_address(&@benton, b"leaderboard");
        let leaderboard = borrow_global<Leaderboard>(leaderboard_addr);
        leaderboard.entries
    }

    #[view]
    public fun get_player_score(player: address): u64 acquires Leaderboard {
        let leaderboard_addr = object::create_object_address(&@benton, b"leaderboard");
        let leaderboard = borrow_global<Leaderboard>(leaderboard_addr);
        *table::borrow(&leaderboard.scores, player)
    }

    #[test_only]
    use aptos_framework::account;

    #[test(admin = @benton)]
    public entry fun test_leaderboard(admin: signer) acquires Leaderboard {
        let admin_addr = signer::address_of(&admin);
        account::create_account_for_test(admin_addr);
        
        initialize(&admin);
        
        let player1 = account::create_account_for_test(@0x1);
        let player2 = account::create_account_for_test(@0x2);
        
        update_score(&player1, 100);
        update_score(&player2, 200);
        
        let top_players = get_top_players();
        assert!(vector::length(&top_players) == 2, 0);
        assert!(vector::borrow(&top_players, 0).score == 200, 1);
        assert!(vector::borrow(&top_players, 1).score == 100, 2);
        
        update_score(&player1, 300);
        
        top_players = get_top_players();
        assert!(vector::borrow(&top_players, 0).score == 300, 3);
        assert!(vector::borrow(&top_players, 1).score == 200, 4);
        
        assert!(get_player_score(@0x1) == 300, 5);
        assert!(get_player_score(@0x2) == 200, 6);
    }
}
